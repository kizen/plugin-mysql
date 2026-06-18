import pymysql
from pymysql.cursors import DictCursor

def connect_to_mysql():

  outputs.log(f'Secret: {secrets}')

  secret_password = next(iter(key for key in secrets if key.endswith("mysql_password")), None)
  MYSQL_PASSWORD = secrets[secret_password]

  secret_host = next(iter(key for key in secrets if key.endswith("mysql_host")), None)
  MYSQL_HOST = secrets[secret_host]

  secret_port = next(iter(key for key in secrets if key.endswith("mysql_port")), None)
  MYSQL_PORT = secrets[secret_port]

  INPUT_USER = inputs.user
  outputs.log(f'INPUT_USER: {INPUT_USER}')

  INPUT_DATABASE = inputs.database
  outputs.log(f'INPUT_DATABASE: {INPUT_DATABASE}')

  INPUT_QUERY = inputs.query
  outputs.log(f'INPUT_QUERY: {INPUT_QUERY}')

  connection_config = {
      'host': MYSQL_HOST,
      'port': int(MYSQL_PORT),
      'user': INPUT_USER,
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
          for row in rows:
              outputs.log(row)
              outputs.result = str(next(iter(row.values())))
      
      return connection
      
  except pymysql.MySQLError as e:
      outputs.log(f"Error connecting to MySQL: {e}")
      return None
  
  finally:
      if 'connection' in locals() and connection and connection.open:
          connection.close()
          outputs.log("MySQL connection closed")

db_connection = connect_to_mysql()
