import http.client
import json
import uuid

# PAT config
SNOWFLAKE_ACCOUNT = "yhjtexo-kv44817"  # host without .snowflakecomputing.com
SNOWFLAKE_PAT = "eyJraWQiOiI0MDk5NjA2NDEzNjU2MDcwIiwiYWxnIjoiRVMyNTYifQ.eyJwIjoiMjQ0MzU1NTg4OjYyNTU1MDI5NzY1IiwiaXNzIjoiU0Y6MTAxNiIsImV4cCI6MTc4ODgwMDg1OH0.fc9xJVwZLLmN76D_ewx51O_iWtXAg-o6kCeUSmay5XY2R4W6QGt1FwWw99orvmYG61i335Cr6UEfz8tR4K_ylA"  # Your PAT from ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN

# outputs.log(f'Secret: {secrets["webhook_url_scott_fs_snowflake_pat_secret"]}')

conn = http.client.HTTPSConnection(f"{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com")
payload = json.dumps({
  "statement": "SELECT * FROM TEST_DB.PUBLIC.TEST_CUSTOMERS",
  "timeout": 1000,
  "database": "TEST_DB",
  "schema": "PUBLIC",
  "warehouse": "COMPUTE_WH",
  "bindings": {},
  "parameters": {},
  "role": "SYSADMIN"
})
headers = {
  'User-Agent': 'myApplication/1.0',
  'X-Snowflake-Authorization-Token-Type': 'PROGRAMMATIC_ACCESS_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': f'Bearer {SNOWFLAKE_PAT}'
}

request_id = str(uuid.uuid4())  # Generate unique requestId each time
conn.request("POST", f"/api/v2/statements?requestId={request_id}&async=false", payload, headers)
res = conn.getresponse()

outputs.log(res)

data = res.read()
outputs.log(data.decode("utf-8"))
