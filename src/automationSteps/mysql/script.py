import mysql.connector
from mysql.connector import Error

try:
    # 1. Establish the connection to the database
    connection = mysql.connector.connect(
        host="localhost",        # Replace with your server IP if remote
        user="root",             # Your MySQL username
        password="test12345", # Your MySQL password
        database="demodb" # The database you want to use
    )

    if connection.is_connected():
        outputs.log("Successfully connected to the MySQL database!")
        
        # 2. Create a cursor object to execute SQL commands
        cursor = connection.cursor()
        
        # 3. Execute a basic query
        cursor.execute("SELECT * FROM users;")
        
        # 4. Fetch and display all result records
        rows = cursor.fetchall()
        for row in rows:
            outputs.log(row)

except Error as e:
    # Handle connection or SQL execution errors safely
    outputs.log(f"Error while connecting to MySQL: {e}")

finally:
    # 5. Guarantee that resource handles are closed on exit
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        outputs.log("MySQL connection safely closed.")
