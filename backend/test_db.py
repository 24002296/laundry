from database import get_connection

connection = get_connection()

if connection:

    print("Connected Successfully!")

    connection.close()

else:

    print("Connection Failed.")