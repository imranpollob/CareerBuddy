#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local/dynamodb-local .local/dynamodb-data
if [ ! -f .local/dynamodb-local/DynamoDBLocal.jar ]; then
  curl -fsSL https://d1ni2b6xgvw0s0.cloudfront.net/v2.x/dynamodb_local_latest.tar.gz -o .local/dynamodb-local.tar.gz
  tar -xzf .local/dynamodb-local.tar.gz -C .local/dynamodb-local
fi
exec java -Djava.library.path=.local/dynamodb-local/DynamoDBLocal_lib \
  -jar .local/dynamodb-local/DynamoDBLocal.jar -sharedDb -dbPath .local/dynamodb-data -port 8001 -disableTelemetry
