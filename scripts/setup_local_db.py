"""Create the SkillPilot table on DynamoDB LOCAL only. Never targets AWS."""
import argparse
from urllib.parse import urlparse
import boto3


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--endpoint",default="http://127.0.0.1:8001")
    args=parser.parse_args()
    if urlparse(args.endpoint).hostname not in {"127.0.0.1","localhost","::1"}:
        raise SystemExit("Refusing to create a table outside a loopback endpoint")
    client=boto3.client("dynamodb",endpoint_url=args.endpoint,region_name="us-east-1",
                        aws_access_key_id="local",aws_secret_access_key="local")
    if "SkillPilot" in client.list_tables()["TableNames"]:
        print("Local SkillPilot table already exists")
        return
    client.create_table(TableName="SkillPilot",BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName":"PK","KeyType":"HASH"},{"AttributeName":"SK","KeyType":"RANGE"}],
        AttributeDefinitions=[{"AttributeName":"PK","AttributeType":"S"},{"AttributeName":"SK","AttributeType":"S"}])
    client.get_waiter("table_exists").wait(TableName="SkillPilot")
    print("Created SkillPilot on DynamoDB Local; no AWS infrastructure created")


if __name__=="__main__":
    main()
