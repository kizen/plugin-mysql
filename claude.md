Plugin Overview
This repo contains the MySQL integration plugin for Kizen's Agentic Workflow engine. It adds a read-only Run Query action step that connects to external MySQL instances, executes parameterized SELECT queries, and returns results to workflow context.

Pillar: Expand
Epic: KZN-17383
Feasibility Spike: KZN-17261
Container Dependency: KZN-17366 - mysqlclient must be in agentic-workflow container image

1. Key Architecture Decisions
Decision

Rationale

Driver: pymysql not mysqlclient

Pure Python, no C dependencies. Avoids container build complexity. mysqlclient was originally specced but pymysql is used in v1 for portability.

Read-only v1

Limits blast radius and security review scope. No write operations, DDL, or stored procs. Only SELECT allowed.

Named Connections

Matches pattern from Slack/Zoom plugins. Allows multiple DBs per org. Credentials encrypted via Kizen Secrets Manager.

Direct TCP, no tunneling

v1 requires customer to expose DB with IP allowlist. SSH/VPC peering is future phase to reduce scope.

Result format: string

Single cell returns as string. Multi-row/column returns as JSON-encoded string. Keeps workflow variable type consistent. Empty result = "".

10s connect timeout

Prevents hung workers. MySQL query timeout is governed by server max_execution_time.

2. Connection + Secrets Pattern
Secrets are not passed directly. The plugin expects secrets to be stored in Kizen Secrets Manager with specific suffixes:

Required secret suffixes:

mysql_host : MySQL hostname or IP
mysql_port : Port as string, cast to int
mysql_password : Password for the user
Required inputs:

inputs.user : MySQL username
inputs.database : Target database name
inputs.query : SQL SELECT statement
Secret resolution logic:

Python
secret_password = next(iter(key for key in secrets if key.endswith("mysql_password")), None)
MYSQL_PASSWORD = secrets[secret_password]
This allows multiple MySQL connections to coexist in one org without collision.

SSL: Handled by pymysql defaults. ssl_mode from connection config is not yet wired in v1. Default is PREFERRED. For VERIFY_CA, cert upload will be added in KZN-XXXXY.

3. Security Rules
No SQL injection: Do not concatenate user input into inputs.query without parameterization. v1 relies on workflow authors to use safe queries. Future: add automatic variable binding for {{workflow_vars}}.
Principle of least privilege: Docs must tell customers to create read-only MySQL user: GRANT SELECT ON db.* TO 'kizen_ro'@'%';
No credential logging: Never log MYSQL_PASSWORD, connection_config, or full DSN. Host and port are ok to log for debugging.
Query allowlist: Only SELECT statements. Reject queries starting with INSERT, UPDATE, DELETE, DROP, CREATE, ALTER. This is not enforced in code yet - add guard in KZN-XXXXZ.
Error messages: Return clean errors to user. Database connection failed: check credentials and network allowlist. Full traceback goes to internal logs only.
4. Code Entry Points
File

Purpose

main.py

Entry point. Exports connect_to_mysql() called by workflow runner.

main.py:connect_to_mysql()

Resolves secrets, builds connection, executes query, formats output, closes connection.

requirements.txt

pymysql>=1.1.0 required. Blocked until KZN-17366 merges.

Output contract:

outputs.result : Always string. Set by plugin.
outputs.log() : Internal logging only. Not shown to user unless error.
Result shaping logic:

No rows → outputs.result = ""
1 row, 1 column → outputs.result = str(value)
Else → outputs.result = str(rows) where rows is list of dicts from DictCursor
5. Testing
Unit tests: tests/test_mysql.py using pytest + pymysql mocking
Run: pytest tests/

Required test cases:

Connection success with valid creds
Connection fail with bad host → clean error
Query returns single value → string result
Query returns multiple rows → JSON string result
Query returns empty → "" result
Secret resolution finds correct suffix

E2E blocked: Cannot run in workflow until KZN-17366 adds pymysql to container.

6. Error Handling Patterns
Match existing plugin UI pattern:

Error Type

User Message

Internal Log

Auth failure

Database connection failed: check credentials and network allowlist

pymysql.err.OperationalError: (1045, "Access denied...")

Network timeout

Database connection failed: check credentials and network allowlist

pymysql.err.OperationalError: (2003, "Can't connect...")

Query error

Query error: {mysql_error}

Full SQL + traceback

Empty result

No error. Returns ""

Query returned no rows

Notify Plugin Developer toggle: Available in UI. When enabled, errors trigger Slack alert to #workflow-plugins.

7. Local Development
Clone repo: git clone git@github.com:kizen/plugin-mysql.git
Install deps: pip install -r requirements.txt
Set env vars to mimic Kizen secrets: export MYSQL_HOST=localhost ...
Run: python main.py with mocked inputs, outputs, secrets
Docker: Use agentic-workflow image once KZN-17366 merges.

8. Future Work / Out of Scope for v1
Ticket

Description

KZN-XXXXY

Support SSL CA cert upload + VERIFY_CA mode

KZN-XXXXZ

Query validator to block non-SELECT statements

KZN-XXXA1

SSH tunneling for private DBs

KZN-XXXA2

Write operations: INSERT/UPDATE with approval gates

KZN-XXXA3

Schema introspection for field picker UI

KZN-XXXA4

Scheduled Hydrate syncs from MySQL to Kizen custom objects

KZN-XXXA5

Automatic parameterization of {{variables}} to prevent SQLi

9. Gotchas
Port must be int: pymysql.connect(port=int(MYSQL_PORT)) or it fails silently.
Charset: Always use utf8mb4 to support emoji and full Unicode.
DictCursor required: Downstream logic expects dict rows, not tuples.
Connection not reused: New connection per execution. No pooling in v1 to keep it simple.
String serialization: outputs.result = str(rows) uses Python str() not json.dumps(). Downstream steps must json.loads() if needed. Document this for workflow authors.
