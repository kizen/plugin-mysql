# MySQL Connector Module

## Overview

## Files

### 1. `mysql_read`
**Purpose**: Read-only queries against Snowflake. Returns query results as strings.

**Key Features**
- **Read-only guardrail**: Regex check blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, `COPY`, `CALL`, `DO`. Only `SELECT` queries should pass.
- **Smart quote normalization**: Converts curly quotes `“”‘’` to straight quotes before `json.loads()` to handle copy-paste from docs.
- **Multi-env support**: Reads `MYSQL_CONNECTION` secret. If `inputs.connection_secret_tag` is set, uses that nested key. Otherwise treats the secret as flat.
- **Single value mode**: Set `inputs.return_single_value = True` to extract one cell. Throws if query returns >1 row or >1 column.

### 2. `mysql_write`  
**Purpose**: Write operations against Snowflake. Returns stats + results.

**Key Features**
- **No SQL guardrail**: Intentionally allows `INSERT`, `UPDATE`, `DELETE`, etc. Use with caution..
- **Same secret/env handling** as `mysql_read`
- **Single value mode** also supported for write queries that return a value, e.g. `INSERT ... RETURNING id`

## Dependencies

pymysql
Requires DictCursor from pymysql.cursors for dict-based query results.

## Expected Inputs

The function expects these global objects:

secrets: dict
Must contain a key ending in mysql_connection with a JSON string value. Always include production_db as it's the default fallback. Example:

```json
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
```

or, without optional `connection_secret_tag` input field:

```json
{
  "host": "db.prod.example.com",
  "port": 3306,
  "user_name": "app_user",
  "password": "supersecret"
}
```

Note: Handles curly quotes “” by normalizing to straight quotes before json.loads().

inputs: object

- inputs.connection_secret_tag: str - Key to select from MYSQL_CONNECTION dict. If empty, assumes connection info at root of MYSQL_CONNECTION.
- inputs.database: str - Database name to connect to.
- inputs.query: str - SQL query to execute.
- inputs.return_single_value: bool - If True, expects query to return exactly one row with one column. Raises ValueError if multiple rows/columns are returned.

outputs: object
Used for logging and results:

- outputs.log(str) - Logs messages
- outputs.result: str - Set to query result

## Behavior

### Connection Flow

1. Finds secret key in secrets ending with mysql_connection
2. Cleans curly quotes and parses JSON
3. Selects environment using inputs.connection_secret_tag or uses `MYSQL_CONNECTION` as is
4. Extracts host, port, password, user_name
5. Connects to inputs.database with 10s timeout, utf8mb4 charset, DictCursor
6. Logs socket and MySQL version for debugging

### Query Execution

1. Executes inputs.query
2. Result formatting based on inputs.return_single_value:
   - No rows -> outputs.result = ""
   - inputs.return_single_value = True + single row/column -> outputs.result = str(value)
   - inputs.return_single_value = True + multiple rows/columns -> raises ValueError
   - inputs.return_single_value = False + any rows -> outputs.result = str(rows) where rows is list of dicts
3. Always closes connection in finally block

### Error Handling

- json.JSONDecodeError -> logs error, returns None
- KeyError -> logs missing key, returns None
- pymysql.MySQLError -> logs error, raises ValueError(f"Error while using MySQL connection: {e}")
- ValueError -> raised if inputs.return_single_value = True but query doesn't return exactly 1x1 result
- Connection always closed if opened

## Security Notes

1. SQL injection: inputs.query is executed directly with no parameterization. Only use with trusted queries or refactor to use parameterized queries.
2. Port type: Casts MYSQL_PORT to int() - ensure secrets store port as int or string.
3. Error exposure: ValueError raised on pymysql.MySQLError includes the raw MySQL error message, which may leak schema info. Consider sanitizing in production.

## Usage

```python
# Assumes secrets, inputs, outputs are defined in scope
# Set inputs.return_single_value = True for scalar queries
db_connection = connect_to_mysql()
# Result available in outputs.result
print(outputs.result)
```

## Common Issues

| Issue                                          | Cause                                                           | Fix                                           |
| ---------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------- |
| Error decoding JSON                            | Curly quotes or malformed JSON in secret                        | Current code auto-fixes “”. Check JSON syntax |
| Missing key in connection JSON                 | Secret missing host, port, user_name, or password               | Verify secret structure                       |
| Query returned no rows                         | Valid query with empty result set                               | Expected behavior, outputs.result = ""        |
| ValueError: Expected a single value result...  | inputs.return_single_value = True but query returned >1 row/col | Set return_single_value = False or fix query  |
| ValueError: Error while using MySQL connection | MySQL error during connect or query                             | Check logs for specific MySQL error           |

## Suggested Improvements

1. Remove or mask outputs.log(f"MYSQL_CONNECTION raw: {MYSQL_CONNECTION_RAW}") to avoid leaking credentials
2. Add query parameterization instead of raw cursor.execute(INPUT_QUERY)
3. Return native Python types via json.dumps(rows) instead of str(rows) for easier downstream parsing
4. Catch pymysql.MySQLError and return None instead of raising, if you prefer non-exception flow
5. Add autocommit=True to config if running only SELECT statements
