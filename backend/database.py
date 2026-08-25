import mysql.connector
from mysql.connector import Error


def get_connection():
    """
    Creates and returns a connection to MySQL.
    """

    try:

        connection = mysql.connector.connect(

            host="localhost",
            user="root",
            password="B@erlin#12$&",
            database="campus_laundry_connect"

        )

        if connection.is_connected():
            return connection

    except Error as e:

        print("Database Connection Error:", e)

    return None


def execute_query(query, params=None):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(query, params)

        connection.commit()

        cursor.close()
        connection.close()

        return True

    except Exception as e:

        print("DATABASE ERROR:", repr(e))

        if connection:
            connection.rollback()

        if cursor:
            cursor.close()

        if connection:
            connection.close()

        return False
def fetch_one(query, values=None):

    connection = get_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:

        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)

        return cursor.fetchone()

    except Error as e:

        print("Query Error:", e)

        return None

    finally:

        cursor.close()
        connection.close()


def fetch_all(query, values=None):

    connection = get_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:

        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)

        return cursor.fetchall()

    except Error as e:

        print("Query Error:", e)

        return []

    finally:

        cursor.close()
        connection.close()