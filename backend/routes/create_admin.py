import bcrypt

from database import fetch_one, execute_query


def create_admin():

    ADMIN_EMAIL = "admin@laundryconnect.com"
    ADMIN_PASSWORD = "Admin@123"

    # ==========================================
    # CHECK IF ADMIN ALREADY EXISTS
    # ==========================================

    existing_admin = fetch_one(
        """
        SELECT id
        FROM users
        WHERE email = %s
        LIMIT 1
        """,
        (ADMIN_EMAIL,)
    )

    if existing_admin:

        print("====================================")
        print("ADMIN ACCOUNT ALREADY EXISTS")
        print("====================================")

        return


    # ==========================================
    # HASH PASSWORD
    # ==========================================

    hashed_password = bcrypt.hashpw(
        ADMIN_PASSWORD.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


    # ==========================================
    # CREATE ADMIN
    # ==========================================

    success = execute_query(
        """
        INSERT INTO users
        (
            first_name,
            last_name,
            email,
            password,
            role
        )
        VALUES
        (%s, %s, %s, %s, %s)
        """,
        (
            "System",
            "Administrator",
            ADMIN_EMAIL,
            hashed_password,
            "admin"
        )
    )


    if success:

        print("====================================")
        print("ADMIN ACCOUNT CREATED")
        print("====================================")
        print("Email:    admin@laundryconnect.com")
        print("Password: Admin@123")
        print("Role:     admin")
        print("====================================")

    else:

        print("Unable to create admin account.")