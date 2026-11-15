"""Create the CareerBuddy table in AWS DynamoDB (on-demand) and load the job snapshot.

Explicit, opt-in AWS write. Uses the standard credential chain (.env or AWS profile).
The table name comes from SKILLPILOT_TABLE_NAME (sandbox accounts may require a prefix,
for example workshop-skillpilot). Safe to re-run: an existing table is reused and
seeding only adds missing records.
"""
import argparse
import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


def main():
    load_dotenv(".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default=os.getenv("SKILLPILOT_TABLE_NAME", "SkillPilot"))
    parser.add_argument("--region", default=os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "us-east-1")
    args = parser.parse_args()
    client = boto3.client("dynamodb", region_name=args.region)
    try:
        client.create_table(TableName=args.table, BillingMode="PAY_PER_REQUEST",
                            KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
                            AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}, {"AttributeName": "SK", "AttributeType": "S"}],
                            Tags=[{"Key": "app", "Value": "careerbuddy"}])
        print(f"Creating {args.table} in {args.region}…", flush=True)
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceInUseException":
            raise
        print(f"{args.table} already exists; reusing it", flush=True)
    client.get_waiter("table_exists").wait(TableName=args.table)

    from backend.config import Settings
    from backend.db import DynamoRepository
    from backend.service import Service
    settings = Settings(repository="dynamodb", table_name=args.table, seed_accounts=False)
    service = Service(DynamoRepository(args.table, region=args.region), settings)
    service.seed()
    print(f"Ready: {len(service.jobs())} job postings in {args.table}")


if __name__ == "__main__":
    main()
