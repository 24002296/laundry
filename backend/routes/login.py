from flask import Blueprint, request, jsonify
import bcrypt

from database import fetch_one, execute_query

from google.oauth2 import id_token
from google.auth.transport import requests


login = Blueprint("login", __name__)


GOOGLE_CLIENT_ID = "260950180361-6mu307ht07g19btgdo0imfepd1q0f8kf.apps.googleusercontent.com"


# ============================================================
# NORMAL LOGIN
# ============================================================

@login.route("/login", methods=["POST"])
def login_user():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No login information received"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    user = fetch_one(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    stored_password = user.get("password")

    if not stored_password:
        return jsonify({
            "success": False,
            "message": "Invalid user account"
        }), 401

    try:

        password_correct = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8")
        )

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Unable to verify account password"
        }), 500

    if not password_correct:

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    user.pop("password", None)

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": user
    }), 200


# ============================================================
# GOOGLE LOGIN
# ============================================================

@login.route("/google-login", methods=["POST"])
def google_login():

    try:

        data = request.get_json(silent=True)

        if not data or not data.get("credential"):

            return jsonify({
                "success": False,
                "message": "Google credential is required."
            }), 400


        credential = data["credential"]


        # ----------------------------------------------------
        # VERIFY GOOGLE ID TOKEN
        # ----------------------------------------------------

        try:

            google_user = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )

        except ValueError:

            return jsonify({
                "success": False,
                "message": "Invalid Google credential."
            }), 401


        # ----------------------------------------------------
        # GET GOOGLE INFORMATION
        # ----------------------------------------------------

        google_id = google_user.get("sub")
        email = google_user.get("email")
        email_verified = google_user.get(
            "email_verified",
            False
        )

        first_name = google_user.get(
            "given_name",
            ""
        )

        last_name = google_user.get(
            "family_name",
            ""
        )

        profile_picture = google_user.get(
            "picture",
            ""
        )


        if not google_id or not email:

            return jsonify({
                "success": False,
                "message": "Google account information is incomplete."
            }), 400


        if not email_verified:

            return jsonify({
                "success": False,
                "message": "Google email is not verified."
            }), 401


        # ----------------------------------------------------
        # CHECK WHETHER USER ALREADY EXISTS
        # ----------------------------------------------------

        user = fetch_one(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )


        # ----------------------------------------------------
        # CREATE NEW USER
        # ----------------------------------------------------

        if not user:

            execute_query(
                """
                INSERT INTO users
                (
                    first_name,
                    last_name,
                    email,
                    role
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    first_name,
                    last_name,
                    email,
                    "student"
                )
            )


            user = fetch_one(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )


        if not user:

            return jsonify({
                "success": False,
                "message": "Unable to create Google account."
            }), 500


        # ----------------------------------------------------
        # REMOVE PASSWORD
        # ----------------------------------------------------

        user.pop("password", None)


        return jsonify({

            "success": True,

            "message":
                "Google login successful.",

            "user":
                user

        }), 200


    except Exception as error:

        print(
            "GOOGLE LOGIN ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Google login failed.",

            "error":
                str(error)

        }), 500