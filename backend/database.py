import os
import psycopg2
from psycopg2.extras import RealDictCursor


# ============================================================
# GET DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Creates and returns a PostgreSQL connection.

    DATABASE_URL should be configured in Render
    Environment Variables.
    """

    try:

        database_url = os.getenv("DATABASE_URL")

        if not database_url:

            print(
                "Database Connection Error: "
                "DATABASE_URL is not configured."
            )

            return None


        connection = psycopg2.connect(
            database_url
        )


        print(
            "PostgreSQL connection successful."
        )


        return connection


    except Exception as error:

        print(
            "Database Connection Error:",
            repr(error)
        )

        return None


# ============================================================
# EXECUTE INSERT / UPDATE / DELETE
# ============================================================

def execute_query(query, params=None):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:

            return False


        cursor = connection.cursor()


        cursor.execute(
            query,
            params
        )


        connection.commit()


        return True


    except Exception as error:

        print(
            "DATABASE ERROR:",
            repr(error)
        )


        if connection:

            connection.rollback()


        return False


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# ============================================================
# FETCH ONE ROW
# ============================================================

def fetch_one(query, values=None):

    connection = get_connection()

    if connection is None:

        return None


    cursor = connection.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        if values:

            cursor.execute(
                query,
                values
            )

        else:

            cursor.execute(query)


        return cursor.fetchone()


    except Exception as error:

        print(
            "Query Error:",
            repr(error)
        )

        return None


    finally:

        cursor.close()
        connection.close()


# ============================================================
# FETCH MULTIPLE ROWS
# ============================================================

def fetch_all(query, values=None):

    connection = get_connection()

    if connection is None:

        return []


    cursor = connection.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        if values:

            cursor.execute(
                query,
                values
            )

        else:

            cursor.execute(query)


        return cursor.fetchall()


    except Exception as error:

        print(
            "Query Error:",
            repr(error)
        )

        return []


    finally:

        cursor.close()
        connection.close()
