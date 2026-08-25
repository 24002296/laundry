from flask import Blueprint, jsonify, request

from database import fetch_all, fetch_one,execute_query

notifications = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)


# ==========================================================
# GET USER NOTIFICATIONS
# ==========================================================

@notifications.route("/<int:user_id>", methods=["GET"])
def get_notifications(user_id):

    try:

        rows = fetch_all("""
            SELECT
                id,
                user_id,
                title,
                message,
                type,
                reference_id,
                is_read,
                created_at

            FROM notifications

            WHERE user_id = %s

            ORDER BY created_at DESC

            LIMIT 50
        """, (user_id,))


        unread_result = fetch_one("""
            SELECT COUNT(*) AS total

            FROM notifications

            WHERE user_id = %s
            AND is_read = 0
        """, (user_id,))


        return jsonify({

            "success": True,

            "notifications": rows,

            "unread_count":
                unread_result["total"]
                if unread_result
                else 0

        })


    except Exception as error:

        print(
            "GET NOTIFICATIONS ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to load notifications.",

            "error":
                str(error)

        }), 500


# ==========================================================
# MARK ONE NOTIFICATION AS READ
# ==========================================================

@notifications.route(
    "/<int:notification_id>/read",
    methods=["PUT"]
)
def mark_notification_read(notification_id):

    try:

        execute_query("""
            UPDATE notifications

            SET is_read = 1

            WHERE id = %s
        """, (notification_id,))


        return jsonify({

            "success": True

        })


    except Exception as error:

        print(
            "MARK NOTIFICATION ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to update notification."

        }), 500


# ==========================================================
# MARK ALL AS READ
# ==========================================================

@notifications.route(
    "/user/<int:user_id>/read-all",
    methods=["PUT"]
)
def mark_all_read(user_id):

    try:

        execute_query("""
            UPDATE notifications

            SET is_read = 1

            WHERE user_id = %s
            AND is_read = 0
        """, (user_id,))


        return jsonify({

            "success": True

        })


    except Exception as error:

        print(
            "MARK ALL NOTIFICATIONS ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to mark notifications as read."

        }), 500