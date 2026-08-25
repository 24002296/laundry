from flask import Blueprint, request, jsonify

import bcrypt

from database import (
    execute_query,
    fetch_one,
    fetch_all
)

from sms_service import send_sms


register = Blueprint(
    "register",
    __name__
)


# ============================================================
# REGISTER USER
# ============================================================

@register.route(
    "/register",
    methods=["POST"]
)
def register_user():

    print("====================================")
    print("CORRECT REGISTER.PY IS BEING USED")
    print("====================================")

    try:

        data = request.get_json(
            silent=True
        )

        print(
            "REGISTER DATA RECEIVED:",
            data
        )


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No registration data received."

            }), 400


        # ====================================================
        # COMMON FIELDS
        # ====================================================

        first_name = data.get(
            "first_name"
        )

        last_name = data.get(
            "last_name"
        )

        email = data.get(
            "email"
        )

        phone = data.get(
            "phone"
        )

        password = data.get(
            "password"
        )

        role = data.get(
            "role"
        )


        # ====================================================
        # VALIDATION
        # ====================================================

        if not first_name:

            return jsonify({
                "success": False,
                "message":
                    "First name is required."
            }), 400


        if not last_name:

            return jsonify({
                "success": False,
                "message":
                    "Last name is required."
            }), 400


        if not email:

            return jsonify({
                "success": False,
                "message":
                    "Email is required."
            }), 400


        if not phone:

            return jsonify({
                "success": False,
                "message":
                    "Phone number is required."
            }), 400


        if not password:

            return jsonify({
                "success": False,
                "message":
                    "Password is required."
            }), 400


        if not role:

            return jsonify({
                "success": False,
                "message":
                    "Account type is required."
            }), 400


        # ====================================================
        # VALIDATE ROLE
        # ====================================================

        if role not in [
            "student",
            "laundromat"
        ]:

            return jsonify({
                "success": False,
                "message":
                    "Invalid account type."
            }), 400


        # ====================================================
        # CHECK EMAIL
        # ====================================================

        existing_user = fetch_one(

            """
            SELECT id

            FROM users

            WHERE email = %s

            LIMIT 1
            """,

            (email,)

        )


        if existing_user:

            return jsonify({

                "success": False,

                "message":
                    "Email already exists."

            }), 400


        # ====================================================
        # HASH PASSWORD
        # ====================================================

        hashed_password = bcrypt.hashpw(

            password.encode("utf-8"),

            bcrypt.gensalt()

        ).decode("utf-8")


        # ====================================================
        # INSERT USER
        # ====================================================

        user_query = """

            INSERT INTO users (

                first_name,
                last_name,
                email,
                phone,
                password,
                role

            )

            VALUES (

                %s,
                %s,
                %s,
                %s,
                %s,
                %s

            )

        """


        success = execute_query(

            user_query,

            (
                first_name,
                last_name,
                email,
                phone,
                hashed_password,
                role
            )

        )


        if not success:

            return jsonify({

                "success": False,

                "message":
                    "Unable to create user account."

            }), 500


        # ====================================================
        # GET NEW USER ID
        # ====================================================

        new_user = fetch_one(

            """
            SELECT
                id,
                phone

            FROM users

            WHERE email = %s

            LIMIT 1
            """,

            (email,)

        )


        if not new_user:

            return jsonify({

                "success": False,

                "message":
                    "User was created but user ID could not be found."

            }), 500


        user_id = new_user["id"]


        # ====================================================
        # STUDENT
        # ====================================================

        if role == "student":

            student_number = data.get(
                "student_number"
            )


            if not student_number:

                return jsonify({

                    "success": False,

                    "message":
                        "Student number is required."

                }), 400


            student_success = execute_query(

                """
                INSERT INTO students
                (
                    user_id,
                    student_number,
                    status
                )

                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,

                (
                    user_id,
                    student_number,
                    "Active"
                )

            )


            if not student_success:

                return jsonify({

                    "success": False,

                    "message":
                        "User created, but student profile could not be created."

                }), 500


            # =================================================
            # FIND ADMIN PHONE NUMBERS
            # =================================================

            admins = fetch_all("""

                SELECT
                    id,
                    first_name,
                    phone

                FROM users

                WHERE role = 'admin'

                AND phone IS NOT NULL

                AND phone != ''

            """)


            # =================================================
            # SMS ADMIN
            # =================================================

            for admin in admins:

                send_sms(

                    admin["phone"],

                    (
                        f"Campus Laundry Connect: "
                        f"New student registration. "
                        f"{first_name} {last_name} "
                        f"has registered. "
                        f"Student number: "
                        f"{student_number}."
                    )

                )


        # ====================================================
        # LAUNDROMAT
        # ====================================================

        elif role == "laundromat":

            business_name = data.get(
                "business_name"
            )

            business_address = data.get(
                "business_address"
            )


            if not business_name:

                return jsonify({

                    "success": False,

                    "message":
                        "Business name is required."

                }), 400


            if not business_address:

                return jsonify({

                    "success": False,

                    "message":
                        "Business address is required."

                }), 400


            laundromat_success = execute_query(

                """
                INSERT INTO laundromats
                (
                    user_id,
                    business_name,
                    business_address,
                    rating,
                    bookings,
                    status
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,

                (
                    user_id,
                    business_name,
                    business_address,
                    0,
                    0,
                    "Pending"
                )

            )


            if not laundromat_success:

                return jsonify({

                    "success": False,

                    "message":
                        "User created, but laundromat profile could not be created."

                }), 500


            # =================================================
            # FIND ADMIN PHONE NUMBERS
            # =================================================

            admins = fetch_all("""

                SELECT
                    id,
                    first_name,
                    phone

                FROM users

                WHERE role = 'admin'

                AND phone IS NOT NULL

                AND phone != ''

            """)


            # =================================================
            # SMS ADMIN
            # =================================================

            for admin in admins:

                send_sms(

                    admin["phone"],

                    (
                        f"Campus Laundry Connect: "
                        f"New laundromat registration. "
                        f"{business_name} "
                        f"has registered and is "
                        f"awaiting approval."
                    )

                )


        # ====================================================
        # SUCCESS
        # ====================================================

        return jsonify({

            "success": True,

            "message":
                "Registration successful."

        }), 201


    except Exception as error:

        print(
            "REGISTER ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Registration failed.",

            "error":
                str(error)

        }), 500