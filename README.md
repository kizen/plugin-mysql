# plugin-mysql

Kizen MySQL Connector — connect an external MySQL database to Kizen Agentic Workflows for real-time data lookups and writes.

## Automation Steps

### `mysql_read` (Read Data)
Read-only queries against MySQL. Returns query results as strings.

- **Read-only guardrail**: Blocks queries starting with write/DDL keywords (`INSERT`, `UPDATE`, `DELETE`, `REPLACE`, `CREATE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `LOAD`, `CALL`) and sets the session to `TRANSACTION READ ONLY` before executing.
- **Smart quote normalization**: Converts curly quotes `“”‘’` to straight quotes before `json.loads()` to handle copy-paste from docs.
- **Multi-env support**: Reads the `mysql_connection` secret. If `connection_secret_tag` is set, uses that nested key. Otherwise treats the secret as flat.
- **Single value mode**: Set `return_single_value = true` to extract one cell. Throws if the query returns more than one row or column.

### `mysql_write` (Write Data)
Write operations against MySQL. Returns affected row count for write queries (no result set) or query results as strings when a result set is returned.

- **No SQL guardrail**: Intentionally allows `INSERT`, `UPDATE`, `DELETE`, etc. Use with caution.
- Same secret/env handling as `mysql_read`.
- Single value mode also supported for write queries that return a value.

## Dependencies

- `pymysql` (uses `DictCursor` from `pymysql.cursors` for dict-based query results)

## Secrets

Both steps expect a secret named `mysql_connection` containing a JSON string. In the nested form, set `connection_secret_tag` to the environment key to use (e.g., `production_db`).

Multi-environment (nested) form:

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

Single-environment (flat) form — used when `connection_secret_tag` is left empty:

```json
{
  "host": "db.prod.example.com",
  "port": 3306,
  "user_name": "app_user",
  "password": "supersecret"
}
```

Curly quotes (`“” ‘’`) in the secret value are auto-normalized to straight quotes before parsing.

## Inputs

| Input | Type | Required | Description |
| --- | --- | --- | --- |
| `database` | string | yes | Database name to connect to |
| `query` | string | yes | SQL query to execute |
| `return_single_value` | boolean | yes | If true, expects exactly one row with one column; raises if the query returns more |
| `connection_secret_tag` | string | no | Key to select from the `mysql_connection` secret. If empty, the secret is treated as flat |

## Behavior

**Connection flow**
1. Finds the secret key ending in `mysql_connection`.
2. Normalizes curly quotes and parses the JSON.
3. Selects the environment via `connection_secret_tag`, or uses the secret as-is if flat.
4. Extracts `host`, `port`, `user_name`, `password`.
5. Connects to the given `database` with a 10s timeout, `utf8mb4` charset, and `DictCursor`.

**Query execution**
- No rows returned → `result = ""`
- `return_single_value = true` + single row/column → `result = str(value)`
- `return_single_value = true` + multiple rows/columns → raises `ValueError`
- `return_single_value = false` + any rows → `result = str(rows)` (list of dicts)
- Connection is always closed, whether the query succeeds or fails.

## Security Notes

- **SQL injection**: The query input is executed directly with no parameterization. Only use with trusted queries.
- **Error exposure**: Errors raised on a MySQL failure include the raw MySQL error message, which may leak schema info.
- `mysql_write` intentionally allows write/DDL statements — scope secrets and credentials accordingly.

## Common Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| Error decoding JSON | Curly quotes or malformed JSON in the secret | Curly quotes auto-fix; check the rest of the JSON syntax |
| Missing required key(s) | Secret missing `host`, `port`, `user_name`, or `password` | Verify the secret structure |
| Query returned no rows | Valid query with an empty result set | Expected behavior — `result` is `""` |
| `Expected a single value result...` | `return_single_value = true` but the query returned more than one row/column | Set `return_single_value = false` or adjust the query |
| `Error while using MySQL connection` | MySQL error during connect or query | Check the logged MySQL error for details |

## License

GPL-2.0 — see [LICENSE.md](LICENSE.md).
