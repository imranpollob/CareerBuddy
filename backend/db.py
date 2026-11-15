"""Single-table persistence; no repository constructor creates AWS resources."""
from copy import deepcopy
from threading import RLock
from typing import Protocol
import json
from decimal import Decimal
from urllib.parse import urlparse
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


class Conflict(Exception):
    pass


class Repository(Protocol):
    def get(self, pk: str, sk: str) -> dict | None: ...
    def partition(self, pk: str, prefix: str = "") -> list[dict]: ...
    def scan(self, sk: str) -> list[dict]: ...
    def write(self, items: list[dict], pending: tuple[str, str] | None = None, absent: tuple[str, str] | None = None, expected_revision: tuple[str, str, int] | None = None) -> None: ...


def item(pk: str, sk: str, data: dict) -> dict:
    value = {"PK": pk, "SK": sk, "data": data}
    # boto3 returns Decimal values when records are reloaded. Preserve them for
    # DynamoDB writes while using their JSON numeric form for the size guard.
    def numeric(value):
        if isinstance(value,Decimal):
            return int(value) if value==value.to_integral_value() else float(value)
        raise TypeError("Record contains a non-JSON value")
    if len(json.dumps(value,default=numeric).encode()) > 350_000:
        raise ValueError("Record exceeds the MVP item size limit")
    return value


class MemoryRepository:
    def __init__(self):
        self.items = {}
        self.lock = RLock()

    def get(self, pk, sk):
        with self.lock:
            return deepcopy(self.items.get((pk, sk), {}).get("data"))

    def partition(self, pk, prefix=""):
        with self.lock:
            return [deepcopy(v["data"]) for (p, s), v in sorted(self.items.items())
                    if p == pk and s.startswith(prefix)]

    def scan(self, sk):
        with self.lock:
            return [deepcopy(v["data"]) for (_, s), v in sorted(self.items.items()) if s == sk]

    def write(self, items, pending=None, absent=None, expected_revision=None):
        with self.lock:
            if expected_revision:
                pk,sk,revision=expected_revision
                if (self.get(pk,sk) or {}).get("revision")!=revision:
                    raise Conflict("This conversation changed. Refresh and try again.")
            if absent and absent in self.items:
                raise Conflict("Account already exists")
            if pending and self.get(*pending).get("status") != "pending":
                raise Conflict("Assessment has already been submitted")
            for value in items:
                self.items[(value["PK"], value["SK"])] = deepcopy(value)


class DynamoRepository:
    def __init__(self, table_name="SkillPilot", endpoint=None, region=None):
        kwargs = {"region_name": region or boto3.Session().region_name or "us-east-1"}
        if endpoint:
            if urlparse(endpoint).hostname not in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("DynamoDB Local endpoint must use loopback")
            kwargs.update(endpoint_url=endpoint, aws_access_key_id="local", aws_secret_access_key="local")
        self.table = boto3.resource("dynamodb", **kwargs).Table(table_name)
        self.client = self.table.meta.client
        self.name = table_name

    def get(self, pk, sk):
        return self.table.get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=True).get("Item", {}).get("data")

    def partition(self, pk, prefix=""):
        args = {"KeyConditionExpression": Key("PK").eq(pk) & Key("SK").begins_with(prefix), "ConsistentRead": True}
        return self._pages(self.table.query, args)

    def scan(self, sk):
        return self._pages(self.table.scan, {"FilterExpression": Attr("SK").eq(sk), "ConsistentRead": True})

    @staticmethod
    def _pages(operation, args):
        result = []
        while True:
            page = operation(**args)
            result.extend(v["data"] for v in page["Items"])
            if "LastEvaluatedKey" not in page:
                return result
            args["ExclusiveStartKey"] = page["LastEvaluatedKey"]

    def write(self, items, pending=None, absent=None, expected_revision=None):
        # Resource client performs DynamoDB serialization, including nested data.
        writes = []
        for value in items:
            put = {"TableName": self.name, "Item": value}
            if pending == (value["PK"], value["SK"]):
                put.update(ConditionExpression="#d.#s = :pending",
                           ExpressionAttributeNames={"#d": "data", "#s": "status"},
                           ExpressionAttributeValues={":pending": "pending"})
            if absent == (value["PK"], value["SK"]):
                put.update(ConditionExpression="attribute_not_exists(PK)")
            if expected_revision and expected_revision[:2] == (value["PK"],value["SK"]):
                put.update(ConditionExpression="#d.#r = :revision",
                           ExpressionAttributeNames={"#d":"data","#r":"revision"},
                           ExpressionAttributeValues={":revision":expected_revision[2]})
            writes.append({"Put": put})
        try:
            self.client.transact_write_items(TransactItems=writes)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "TransactionCanceledException":
                raise Conflict("Record already exists or has changed") from exc
            raise
