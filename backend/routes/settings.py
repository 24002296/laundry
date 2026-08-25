from flask import Blueprint, request, jsonify
from database import fetch_one, execute_query

settings = Blueprint("settings", __name__)


# ==========================================================
# GET SYSTEM SETTINGS
# ==========================================================

@settings.route("/settings", methods=["GET"])
def get_settings():

    try:

        result = fetch_one("""
            SELECT
                id,
                admin_name,
                admin_email,
                system_name,
                support_email,
                currency,
                email_notification,
                sms_notification,
                booking_notification,
                payment_notification
            FROM system_settings
            WHERE id = 1
            LIMIT 1
        """)

        # If settings don't exist yet
        if not result:

            return jsonify({
                "success": True,
                "settings": {
                    "admin_name": "",
                    "admin_email": "",
                    "system_name": "LaundryConnect",
                    "support_email": "",
                    "currency": "South African Rand (ZAR)",
                    "email_notification": False,
                    "sms_notification": False,
                    "booking_notification": False,
                    "payment_notification": False
                }
            })

        return jsonify({
            "success": True,
            "settings": result
        })

    except Exception as error:

        print(
            "GET SETTINGS ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to load system settings.",
            "error": str(error)
        }), 500


# ==========================================================
# UPDATE SYSTEM SETTINGS
# ==========================================================

@settings.route("/settings", methods=["PUT"])
def update_settings():

    try:

        data = request.get_json() or {}

        system_name = data.get(
            "system_name",
            "LaundryConnect"
        )

        support_email = data.get(
            "support_email",
            ""
        )

        currency = data.get(
            "currency",
            "South African Rand (ZAR)"
        )

        email_notification = data.get(
            "email_notification",
            False
        )

        sms_notification = data.get(
            "sms_notification",
            False
        )

        booking_notification = data.get(
            "booking_notification",
            False
        )

        payment_notification = data.get(
            "payment_notification",
            False
        )


        # Check if settings already exist
        existing = fetch_one("""
            SELECT id
            FROM system_settings
            WHERE id = 1
            LIMIT 1
        """)


        if existing:

            success = execute_query("""
                UPDATE system_settings

                SET
                    system_name = %s,
                    support_email = %s,
                    currency = %s,
                    email_notification = %s,
                    sms_notification = %s,
                    booking_notification = %s,
                    payment_notification = %s

                WHERE id = 1
            """, (
                system_name,
                support_email,
                currency,
                email_notification,
                sms_notification,
                booking_notification,
                payment_notification
            ))

        else:

            success = execute_query("""
                INSERT INTO system_settings (
                    id,
                    system_name,
                    support_email,
                    currency,
                    email_notification,
                    sms_notification,
                    booking_notification,
                    payment_notification
                )

                VALUES (
                    1,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                system_name,
                support_email,
                currency,
                email_notification,
                sms_notification,
                booking_notification,
                payment_notification
            ))


        if not success:

            return jsonify({
                "success": False,
                "message":
                    "Unable to save system settings."
            }), 500


        return jsonify({
            "success": True,
            "message":
                "System settings saved successfully."
        })


    except Exception as error:

        print(
            "UPDATE SETTINGS ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message":
                "Unable to save system settings.",
            "error": str(error)
        }), 500