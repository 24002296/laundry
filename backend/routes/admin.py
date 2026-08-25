from flask import Blueprint, request, jsonify

from database import fetch_one, fetch_all, execute_query
from flask import Blueprint, request, jsonify



from datetime import datetime, date, time, timedelta
from decimal import Decimal
admin = Blueprint("admin", __name__)

admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)
# ==========================================================
# CONVERT DATABASE VALUES TO JSON-SAFE VALUES
# ==========================================================

def serialize_value(value):

    # Decimal -> float
    if isinstance(value, Decimal):
        return float(value)

    # timedelta -> HH:MM:SS
    if isinstance(value, timedelta):

        total_seconds = int(value.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    # datetime -> string
    if isinstance(value, datetime):
        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # date -> string
    if isinstance(value, date):
        return value.strftime(
            "%Y-%m-%d"
        )

    # time -> string
    if isinstance(value, time):
        return value.strftime(
            "%H:%M:%S"
        )

    return value


def serialize_rows(rows):

    if not rows:
        return []

    serialized = []

    for row in rows:

        new_row = {}

        for key, value in row.items():

            new_row[key] = serialize_value(value)

        serialized.append(new_row)

    return serialized
# ==========================================================
# UPDATE ADMIN PROFILE
# ==========================================================

@admin.route("/profile", methods=["PUT"])
def update_admin_profile():

    try:

        data = request.get_json() or {}

        admin_name = data.get("admin_name")
        admin_email = data.get("admin_email")

        if not admin_name:

            return jsonify({
                "success": False,
                "message": "Administrator name is required."
            }), 400

        if not admin_email:

            return jsonify({
                "success": False,
                "message": "Administrator email is required."
            }), 400


        # Split full name
        parts = admin_name.strip().split(" ", 1)

        first_name = parts[0]

        last_name = (
            parts[1]
            if len(parts) > 1
            else ""
        )


        success = execute_query("""
            UPDATE users

            SET
                first_name = %s,
                last_name = %s,
                email = %s

            WHERE role = 'admin'

            LIMIT 1
        """, (
            first_name,
            last_name,
            admin_email
        ))


        if not success:

            return jsonify({
                "success": False,
                "message":
                    "Unable to update administrator profile."
            }), 500


        return jsonify({
            "success": True,
            "message":
                "Administrator profile updated successfully."
        })


    except Exception as error:

        print(
            "UPDATE ADMIN PROFILE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message":
                "Unable to update administrator profile.",
            "error": str(error)
        }), 500

# ==========================================================
# GET ADMIN PROFILE
# ==========================================================

@admin.route("/profile", methods=["GET"])
def get_admin_profile():

    try:

        user = fetch_one("""
            SELECT
                id,
                first_name,
                last_name,
                email,
                role
            FROM users
            WHERE role = 'admin'
            LIMIT 1
        """)

        if not user:

            return jsonify({
                "success": False,
                "message": "Administrator not found."
            }), 404

        return jsonify({
            "success": True,
            "user": user
        })

    except Exception as error:

        print(
            "GET ADMIN PROFILE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to load administrator profile.",
            "error": str(error)
        }), 500
# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@admin.route("/dashboard", methods=["GET"])
def admin_dashboard():

    try:

        # ==================================================
        # TOTAL STUDENTS
        # ==================================================

        student_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM students
            """
        )

        total_students = (
            student_result.get("total", 0)
            if student_result
            else 0
        )


        # ==================================================
        # TOTAL LAUNDROMATS
        # ==================================================

        laundromat_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM laundromats
            """
        )

        total_laundromats = (
            laundromat_result.get("total", 0)
            if laundromat_result
            else 0
        )


        # ==================================================
        # TOTAL BOOKINGS
        # ==================================================

        booking_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM bookings
            """
        )

        total_bookings = (
            booking_result.get("total", 0)
            if booking_result
            else 0
        )


        # ==================================================
        # COMPLETED BOOKINGS
        # ==================================================

        completed_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status = 'Completed'
            """
        )

        completed_bookings = (
            completed_result.get("total", 0)
            if completed_result
            else 0
        )


        # ==================================================
        # PROCESSING BOOKINGS
        # ==================================================

        processing_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status IN (
                'Confirmed',
                'Processing',
                'Washing',
                'Drying'
            )
            """
        )

        processing_bookings = (
            processing_result.get("total", 0)
            if processing_result
            else 0
        )


        # ==================================================
        # PENDING BOOKINGS
        # ==================================================

        pending_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status = 'Pending'
            """
        )

        pending_bookings = (
            pending_result.get("total", 0)
            if pending_result
            else 0
        )


        # ==================================================
        # CANCELLED BOOKINGS
        # ==================================================

        cancelled_result = fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status = 'Cancelled'
            """
        )

        cancelled_bookings = (
            cancelled_result.get("total", 0)
            if cancelled_result
            else 0
        )


        # ==================================================
        # TOTAL REVENUE
        # ==================================================

        revenue_result = fetch_one(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM bookings
            WHERE status = 'Completed'
            """
        )

        total_revenue = (
            float(revenue_result.get("total", 0))
            if revenue_result
            else 0
        )


        # ==================================================
        # RECENT BOOKINGS
        # ==================================================

        recent_bookings = fetch_all(
            """
            SELECT
                id,
                booking_number,
                student_id,
                laundromat_id,
                service,
                pickup_date,
                pickup_time,
                amount,
                status,
                created_at,
                estimated_completion
            FROM bookings
            ORDER BY id DESC
            LIMIT 5
            """
        )


        # ==================================================
        # SERIALIZE DATABASE VALUES
        # ==================================================

        recent_bookings = serialize_rows(
            recent_bookings
        )


        # ==================================================
        # RESPONSE
        # ==================================================

        return jsonify({

            "success": True,

            "statistics": {

                "total_students":
                    total_students,

                "total_laundromats":
                    total_laundromats,

                "total_bookings":
                    total_bookings,

                # Keep these for compatibility
                # with your existing dashboard

                "total_orders":
                    total_bookings,

                "completed_bookings":
                    completed_bookings,

                "completed_orders":
                    completed_bookings,

                "processing_bookings":
                    processing_bookings,

                "processing_orders":
                    processing_bookings,

                "pending_bookings":
                    pending_bookings,

                "cancelled_bookings":
                    cancelled_bookings,

                "total_revenue":
                    total_revenue
            },

            "recent_bookings":
                recent_bookings,

            # Keep compatibility with old frontend

            "recent_orders":
                recent_bookings

        })


    except Exception as error:

        print(
            "ADMIN DASHBOARD ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to load admin dashboard.",

            "error":
                str(error)

        }), 500

# ============================================================
# ADMIN - SUBSCRIPTION REPORT
# ============================================================

@admin.route("/subscriptions", methods=["GET"])
def get_admin_subscriptions():

    try:

        query = """
            SELECT
                subscriptions.id,
                subscriptions.user_id,
                subscriptions.user_role,
                subscriptions.plan,
                subscriptions.amount,
                subscriptions.payment_method,
                subscriptions.transaction_id,
                subscriptions.status,
                subscriptions.start_date,
                subscriptions.end_date,
                subscriptions.created_at,

                users.first_name,
                users.last_name,
                users.email,

                students.student_number,

                laundromats.business_name

            FROM subscriptions

            INNER JOIN users
                ON subscriptions.user_id = users.id

            LEFT JOIN students
                ON students.user_id = users.id

            LEFT JOIN laundromats
                ON laundromats.user_id = users.id

            ORDER BY subscriptions.created_at DESC
        """

        subscriptions = fetch_all(query)

        result = []

        student_total = Decimal("0.00")
        laundromat_total = Decimal("0.00")

        active_students = 0
        active_laundromats = 0

        now = datetime.now()


        # ====================================================
        # PROCESS SUBSCRIPTIONS
        # ====================================================

        for subscription in subscriptions:

            amount = (
                subscription.get("amount")
                or Decimal("0.00")
            )

            if isinstance(amount, str):
                amount = Decimal(amount)


            role = subscription.get(
                "user_role"
            )

            status = subscription.get(
                "status"
            )

            end_date = subscription.get(
                "end_date"
            )


            # =================================================
            # CHECK ACTIVE
            # =================================================

            is_active = (
                status == "Active"
                and end_date is not None
                and end_date >= now
            )


            # =================================================
            # STUDENT
            # =================================================

            if role == "student":

                student_total += amount

                if is_active:
                    active_students += 1


            # =================================================
            # LAUNDROMAT
            # =================================================

            elif role == "laundromat":

                laundromat_total += amount

                if is_active:
                    active_laundromats += 1


            # =================================================
            # ADD TO RESULT
            # =================================================

            result.append({

                "id":
                    subscription["id"],

                "user_id":
                    subscription["user_id"],

                "role":
                    role,

                "first_name":
                    subscription.get("first_name"),

                "last_name":
                    subscription.get("last_name"),

                "email":
                    subscription.get("email"),

                "student_number":
                    subscription.get(
                        "student_number"
                    ),

                "business_name":
                    subscription.get(
                        "business_name"
                    ),

                "plan":
                    subscription.get("plan"),

                "amount":
                    float(amount),

                "payment_method":
                    subscription.get(
                        "payment_method"
                    ),

                "transaction_id":
                    subscription.get(
                        "transaction_id"
                    ),

                "status":
                    status,

                "start_date":
                    subscription["start_date"].isoformat()
                    if subscription.get("start_date")
                    else None,

                "end_date":
                    subscription["end_date"].isoformat()
                    if subscription.get("end_date")
                    else None,

                "created_at":
                    subscription["created_at"].isoformat()
                    if subscription.get("created_at")
                    else None
            })


        # ====================================================
        # TOTAL REVENUE
        # ====================================================

        total_revenue = (
            student_total +
            laundromat_total
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "subscriptions":
                result,

            "statistics": {

                "total_subscriptions":
                    len(result),

                "active_students":
                    active_students,

                "active_laundromats":
                    active_laundromats,

                "student_revenue":
                    float(student_total),

                "laundromat_revenue":
                    float(laundromat_total),

                "total_revenue":
                    float(total_revenue)
            }

        }), 200


    except Exception as error:

        print(
            "ADMIN SUBSCRIPTION ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to load subscription report.",

            "error":
                str(error)

        }), 500