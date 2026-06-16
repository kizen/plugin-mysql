import pymysql
from pymysql.cursors import DictCursor

def connect_to_mysql():

  target = None

  outputs.log(f'Secret: {secrets}')

  secret_name = next(iter(key for key in secrets if key.endswith("mysql_password")), None)
  
  outputs.log(f'Secret name: {secret_name}')
  MYSQL_PASSWORD = secrets[secret_name]
  outputs.log(f'MYSQL_PASSWORD: {MYSQL_PASSWORD}')

  secret_host = next(iter(key for key in secrets if key.endswith("mysql_host")), None)
  outputs.log(f'Secret name: {secret_host}')
  MYSQL_HOST = secrets[secret_host]
  outputs.log(f'MYSQL_HOST: {MYSQL_HOST}')

  secret_port = next(iter(key for key in secrets if key.endswith("mysql_port")), None)
  outputs.log(f'Secret name: {secret_port}')
  MYSQL_PORT = secrets[secret_port]
  outputs.log(f'MYSQL_PORT: {MYSQL_PORT}')

  connection_config = {
      'host': MYSQL_HOST,
      'port': int(MYSQL_PORT),
      'user': 'ScottF_Kizen',               
      'password': MYSQL_PASSWORD,
      'database': 'demodb',   
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
          
          cursor.execute("SELECT * FROM demodb.users LIMIT 1;")
          rows = cursor.fetchall()
          for row in rows:
              outputs.log(row)
              outputs.target = str(row['age'])
      
      return connection
      
  except pymysql.MySQLError as e:
      outputs.log(f"Error connecting to MySQL: {e}")
      return None
  
  finally:
      if 'connection' in locals() and connection and connection.open:
          connection.close()
          outputs.log("MySQL connection closed")

db_connection = connect_to_mysql()
