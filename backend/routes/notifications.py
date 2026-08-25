from flask import Blueprint, request, jsonify

from database import fetch_all, fetch_one, execute_query


notifications = Blueprint(
    "notifications",
    __name__
)


# ============================================================
# CREATE NOTIFICATION
# ============================================================

def create_notification(
    user_id,
    title,
    message,
    notification_type,
    related_id=None
):

    try:

        query = """
            INSERT INTO notifications (
                user_id,
                title,
                message,
                type,
                related_id
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        success = execute_query(
            query,
            (
                user_id,
                title,
                message,
                notification_type,
                related_id
            )
        )

        return success

    except Exception as error:

        print(
            "CREATE NOTIFICATION ERROR:",
            error
        )

        return False


# ============================================================
# GET USER NOTIFICATIONS
# ============================================================

@notifications.route(
    "/notifications/<int:user_id>",
    methods=["GET"]
)
def get_notifications(user_id):

    try:

        query = """
            SELECT
                id,
                user_id,
                title,
                message,
                type,
                related_id,
                is_read,
                created_at

            FROM notifications

            WHERE user_id = %s

            ORDER BY created_at DESC

            LIMIT 50
        """

        result = fetch_all(
            query,
            (user_id,)
        )

        return jsonify({
            "success": True,
            "notifications": result
        })

    except Exception as error:

        print(
            "GET NOTIFICATIONS ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to load notifications.",
            "error": str(error)
        }), 500


# ============================================================
# GET UNREAD COUNT
# ============================================================

@notifications.route(
    "/notifications/<int:user_id>/unread-count",
    methods=["GET"]
)
def unread_count(user_id):

    try:

        result = fetch_one(
            """
            SELECT COUNT(*) AS total

            FROM notifications

            WHERE user_id = %s

            AND is_read = FALSE
            """,
            (user_id,)
        )

        return jsonify({
            "success": True,
            "count": result["total"] if result else 0
        })

    except Exception as error:

        print(
            "UNREAD COUNT ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to get notification count.",
            "error": str(error)
        }), 500


# ============================================================
# MARK ONE NOTIFICATION AS READ
# ============================================================

@notifications.route(
    "/notifications/<int:id>/read",
    methods=["PUT"]
)
def mark_notification_read(id):

    try:

        execute_query(
            """
            UPDATE notifications

            SET is_read = TRUE

            WHERE id = %s
            """,
            (id,)
        )

        return jsonify({
            "success": True,
            "message": "Notification marked as read."
        })

    except Exception as error:

        print(
            "MARK NOTIFICATION ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to update notification.",
            "error": str(error)
        }), 500


# ============================================================
# MARK ALL AS READ
# ============================================================

@notifications.route(
    "/notifications/<int:user_id>/read-all",
    methods=["PUT"]
)
def mark_all_read(user_id):

    try:

        execute_query(
            """
            UPDATE notifications

            SET is_read = TRUE

            WHERE user_id = %s
            """,
            (user_id,)
        )

        return jsonify({
            "success": True,
            "message": "All notifications marked as read."
        })

    except Exception as error:

        print(
            "MARK ALL NOTIFICATIONS ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to update notifications.",
            "error": str(error)
        }), 500