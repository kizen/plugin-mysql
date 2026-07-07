import json
import pymysql
from pymysql.cursors import DictCursor

def connect_to_mysql():
    secret_connection = next(iter(key for key in secrets if key.endswith("mysql_connection")), None)
    if not secret_connection:
        raise ValueError("No mysql_connections secret found")
    MYSQL_CONNECTION_RAW = secrets[secret_connection]

    # Replace curly quotes with straight quotes
    SMART_QUOTE_MAP = str.maketrans({
        '\u201c': '"',  # “
        '\u201d': '"',  # ”
        '\u2018': "'",  # ‘
        '\u2019': "'",  # ’
        '\u201b': "'",  # ‛ single high-reversed-9
        '\u201e': '"',  # „ double low-9
        '\u201f': '"',  # ‟ double high-reversed-9
    })
    cleaned_json = MYSQL_CONNECTION_RAW.translate(SMART_QUOTE_MAP)
    MYSQL_CONNECTION = json.loads(cleaned_json)

    # Now actually use it - pick which env you want
    conn_data = {}
    if inputs.connection_secret_tag:
      if inputs.connection_secret_tag not in MYSQL_CONNECTION:
          raise ValueError(f"Connection secret tag {inputs.connection_secret_tag} not found in MYSQL_CONNECTION")
      conn_data = MYSQL_CONNECTION[inputs.connection_secret_tag]
    else:
      # If no connection secret tag is provided, MYSQL_CONNECTION isn't nested
      conn_data = MYSQL_CONNECTION

    REQUIRED_KEYS = ('host', 'port', 'user_name', 'password')
    missing_keys = [key for key in REQUIRED_KEYS if key not in conn_data]
    if missing_keys:
        raise ValueError(f"MySQL connection secret is missing required key(s): {', '.join(missing_keys)}")

    MYSQL_HOST = conn_data['host']
    MYSQL_PORT = conn_data['port']
    MYSQL_PASSWORD = conn_data['password']
    MYSQL_USER = conn_data['user_name']

    INPUT_DATABASE = inputs.database
    INPUT_QUERY = inputs.query

    connection_config = {
        'host': MYSQL_HOST,
        'port': int(MYSQL_PORT),
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': INPUT_DATABASE,
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,    
        'connect_timeout': 10,
        'autocommit': True
    }

    outputs.log(f"Using host: {connection_config['host']} and port: {connection_config['port']}")

    try:
        with pymysql.connect(**connection_config) as connection, connection.cursor() as cursor:
            cursor.execute(INPUT_QUERY)

            if cursor.description is None: # True for INSERT/UPDATE/DELETE
                connection.commit() # Commit the transaction for write queries
                outputs.log(f"Rows affected: {cursor.rowcount}")
                outputs.result = str(cursor.rowcount)
            else:
                # Your existing SELECT logic
                rows = cursor.fetchall()
                if not rows:
                    outputs.log("Query returned no rows")
                    outputs.result = ""
                elif inputs.return_single_value:
                    if len(rows) == 1 and len(rows[0]) == 1:
                        single_value = next(iter(rows[0].values()))
                        outputs.log(f"Single value result: {single_value}")
                        outputs.result = str(single_value)
                    else:
                        raise ValueError("Expected a single value result, but the query returned multiple rows or columns.")
                else:
                    outputs.log(f"Multiple values/rows returned: {len(rows)} rows")
                    outputs.result = str(rows)

    except pymysql.MySQLError as e:
        raise ValueError(f"Error while using MySQL connection: {e}")

connect_to_mysql()
