import pymysql
from pymysql.cursors import DictCursor

def connect_to_mysql():
    
  connection_config = {
      'host': 'localhost',
      'port': 3306,
      'user': 'root',               
      'password': 'test12345',
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
          
          cursor.execute("SELECT * FROM demodb.users;")
          rows = cursor.fetchall()
          for row in rows:
              outputs.log(row)
      
      return connection
      
  except pymysql.MySQLError as e:
      outputs.log(f"Error connecting to MySQL: {e}")
      return None
  
  finally:
      if 'connection' in locals() and connection and connection.open:
          connection.close()
          outputs.log("MySQL connection closed")

if __name__ == "__main__":
  db_connection = connect_to_mysql()
