# MySQL Connector Module

## Overview
connect_to_mysql() handles connecting to MySQL using credentials stored in secrets, executes a query from inputs, and returns results via outputs. Built for a serverless/secret-managed environment where connection strings are stored as JSON.

## Dependencies
pymysql
Requires DictCursor from pymysql.cursors for dict-based query results.

## Expected Inputs
The function expects these global objects:

secrets: dict
Must contain a key ending in mysql_connection with a JSON string value. Always include production_db as it's the default fallback. Example:
{
  "production_db": {
    "host": "db.prod.example.com",
    "port": 3306,
    "user_name": "app_user",
    "password": "supersecret"
  },
  "staging_db": {
    "host": "db.staging.example.com", 
    "port": 3306,
    "user_name": "staging_user",
    "password": "stagingpass"
  }
}
Note: Handles curly quotes “” by normalizing to straight quotes before json.loads().

inputs: object
- inputs.connection_secret_tag: str - Key to select from MYSQL_CONNECTION dict. Falls back to 'production_db' if not found.
- inputs.database: str - Database name to connect to.
- inputs.query: str - SQL query to execute.

outputs: object
Used for logging and results:
- outputs.log(str) - Logs messages
- outputs.result: str - Set to query result

## Behavior

### Connection Flow
1. Finds secret key in secrets ending with mysql_connection
2. Cleans curly quotes and parses JSON
3. Selects environment using inputs.connection_secret_tag, default production_db
4. Extracts host, port, password, user_name
5. Connects to inputs.database with 10s timeout, utf8mb4 charset, DictCursor
6. Logs socket and MySQL version for debugging

### Query Execution
1. Executes inputs.query
2. Result formatting:
   - No rows -> outputs.result = ""
   - Single row + single column -> outputs.result = str(value) 
   - Multiple rows/columns -> outputs.result = str(rows) where rows is list of dicts
3. Always closes connection in finally block

### Error Handling
- json.JSONDecodeError -> logs error, returns None
- KeyError -> logs missing key, returns None 
- pymysql.MySQLError -> logs error, returns None
- Connection always closed if opened

## Security Notes
1. Secret logging: outputs.log(f'Secret: {secrets}') logs all secrets in plaintext. Remove in production.
2. SQL injection: inputs.query is executed directly with no parameterization. Only use with trusted queries or refactor to use parameterized queries.
3. Port type: Casts MYSQL_PORT to int() - ensure secrets store port as int or string.

## Usage
# Assumes secrets, inputs, outputs are defined in scope
db_connection = connect_to_mysql()
# Result available in outputs.result
print(outputs.result)

## Common Issues
Issue | Cause | Fix
Error decoding JSON | Curly quotes or malformed JSON in secret | Current code auto-fixes “”. Check JSON syntax
Missing key in connection JSON | Secret missing host, port, user_name, or password | Verify secret structure
Query returned no rows | Valid query with empty result set | Expected behavior, outputs.result = ""
None returned | Connection or JSON error occurred | Check logs for specific exception

## Suggested Improvements
1. Remove outputs.log(f'Secret: {secrets}') to avoid leaking credentials
2. Add query parameterization instead of raw cursor.execute(INPUT_QUERY)
3. Return rows directly instead of str(rows) for easier downstream parsing
4. Add autocommit=True to config if running only SELECT statements
