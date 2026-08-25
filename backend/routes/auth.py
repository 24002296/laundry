from flask import Blueprint, request, jsonify
import bcrypt
from database import execute_query, fetch_one

auth = Blueprint("auth", __name__)


# ==========================
# Register
# ==========================




# ==========================
# Login
# ==========================

@auth.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = fetch_one(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    if user is None:

        return jsonify({
            "success": False,
            "message": "Email not found."
        }), 401

    if bcrypt.checkpw(
        password.encode("utf-8"),
        user["password"].encode("utf-8")
    ):

        user.pop("password")

        return jsonify({

            "success": True,
            "message": "Login successful",
            "user": user

        })

    return jsonify({

        "success": False,
        "message": "Incorrect password"

    }), 401


@auth.route("/change-password", methods=["POST"])
def change_password():

    data = request.get_json()

    print("CHANGE PASSWORD DATA:")
    print(data)

    if not data:

        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400


    user_id = data.get("user_id")
    current_password = data.get("current_password")
    new_password = data.get("new_password")


    # Check required fields
    if not user_id or not current_password or not new_password:

        return jsonify({
            "success": False,
            "message": "All password fields are required."
        }), 400


    # Get user
    user = fetch_one(
        """
        SELECT id, password
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )


    if not user:

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404


    # Check current password
    try:

        password_correct = bcrypt.checkpw(

            current_password.encode("utf-8"),

            user["password"].encode("utf-8")

        )

    except Exception as error:

        print("PASSWORD CHECK ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to verify current password."
        }), 500


    if not password_correct:

        return jsonify({
            "success": False,
            "message": "Current password is incorrect."
        }), 401


    # ==========================
    # HASH NEW PASSWORD
    # ==========================

    hashed_password = bcrypt.hashpw(

        new_password.encode("utf-8"),

        bcrypt.gensalt()

    ).decode("utf-8")


    # ==========================
    # UPDATE DATABASE
    # ==========================

    success = execute_query(

        """
        UPDATE users

        SET password=%s

        WHERE id=%s
        """,

        (
            hashed_password,
            user_id
        )

    )


    if not success:

        return jsonify({
            "success": False,
            "message": "Unable to update password."
        }), 500


    return jsonify({

        "success": True,

        "message": "Password changed successfully."

    })