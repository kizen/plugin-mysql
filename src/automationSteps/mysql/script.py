import json
import pymysql
from pymysql.cursors import DictCursor

def connect_to_mysql():

    try:
        secret_connection = next(iter(key for key in secrets if key.endswith("mysql_connection")), None)
        MYSQL_CONNECTION_RAW = secrets[secret_connection]
        outputs.log(f"MYSQL_CONNECTION raw: {MYSQL_CONNECTION_RAW}")

        # Replace curly quotes with straight quotes
        cleaned_json = MYSQL_CONNECTION_RAW.replace('“', '"').replace('”', '"')
        MYSQL_CONNECTION = json.loads(cleaned_json)

        # Now actually use it - pick which env you want
        env = inputs.connection_secret_tag if inputs.connection_secret_tag in MYSQL_CONNECTION else 'production_db'
        conn_data = MYSQL_CONNECTION[env]

        MYSQL_HOST = conn_data['host']
        MYSQL_PORT = conn_data['port']
        MYSQL_PASSWORD = conn_data['password']
        MYSQL_USER = conn_data['user_name']

    except json.JSONDecodeError as e:
        outputs.log(f"Error decoding JSON from connection_secret_tag: {e}")
        return None
    except KeyError as e:
        outputs.log(f"Missing key in connection JSON: {e}")
        return None

    INPUT_DATABASE = inputs.database
    outputs.log(f'INPUT_DATABASE: {INPUT_DATABASE}')

    INPUT_QUERY = inputs.query
    outputs.log(f'INPUT_QUERY: {INPUT_QUERY}')

    connection_config = {
        'host': MYSQL_HOST,
        'port': int(MYSQL_PORT),
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': INPUT_DATABASE,
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,    
        'connect_timeout': 10         
    }

    outputs.log(f"Using host: {connection_config['host']} and port: {connection_config['port']}")

    try:
        connection = pymysql.connect(**connection_config)
        outputs.log("Successfully connected to MySQL database via socket")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@socket, @@version")
            result = cursor.fetchone()
            outputs.log(f"Socket: {result['@@socket']}")
            outputs.log(f"Version: {result['@@version']}")
            
            cursor.execute(INPUT_QUERY)
            rows = cursor.fetchall()

            outputs.log(f"Rows: {rows}")
            
            if not rows:
                outputs.log("Query returned no rows")
                outputs.result = ""
            elif len(rows) == 1 and len(rows[0]) == 1:
                # Single row, single column -> return just that value
                single_value = next(iter(rows[0].values()))
                outputs.log(f"Single value result: {single_value}")
                outputs.result = str(single_value)
            else:
                # Multiple rows or multiple columns -> return entire dataset
                outputs.log(f"Multiple values detected: {len(rows)} rows")
                outputs.result = str(rows)
        
        return connection
        
    except pymysql.MySQLError as e:
        outputs.log(f"Error connecting to MySQL: {e}")
        return None

    finally:
        if 'connection' in locals() and connection and connection.open:
            connection.close()
            outputs.log("MySQL connection closed")

db_connection = connect_to_mysql()
