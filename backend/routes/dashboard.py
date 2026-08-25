from flask import Blueprint, jsonify

from database import fetch_one, fetch_all

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard", methods=["GET"])
def admin_dashboard():

    # Total Students
    students = fetch_one("""

        SELECT COUNT(*) AS total

        FROM students

    """)

    # Total Laundromats
    laundromats = fetch_one("""

        SELECT COUNT(*) AS total

        FROM laundromats

    """)

    # Total Bookings
    bookings = fetch_one("""

        SELECT COUNT(*) AS total

        FROM bookings

    """)

    # Total Revenue
    revenue = fetch_one("""

        SELECT

            IFNULL(SUM(amount),0) AS total

        FROM payments

        WHERE status='Paid'

    """)
    processing = fetch_one("""

        SELECT COUNT(*) AS total

        FROM bookings

        WHERE status='Processing'

    """)

    completed = fetch_one("""

        SELECT COUNT(*) AS total

        FROM bookings

        WHERE status='Completed'

    """)

    cancelled = fetch_one("""

        SELECT COUNT(*) AS total

        FROM bookings

        WHERE status='Cancelled'

    """)
    successful = fetch_one("""

        SELECT COUNT(*) AS total

        FROM payments

        WHERE status='Paid'

    """)

    pending = fetch_one("""

        SELECT COUNT(*) AS total

        FROM payments

        WHERE status='Pending'

    """)

    refunded = fetch_one("""

        SELECT COUNT(*) AS total

        FROM payments

        WHERE status='Refunded'

    """)
    recent_activity = fetch_all("""

        SELECT

            bookings.booking_number,

            CONCAT(users.first_name,' ',users.last_name)
            AS student,

            laundromats.business_name,

            bookings.service,

            bookings.status,

            bookings.created_at

        FROM bookings

        INNER JOIN students

            ON bookings.student_id=students.id

        INNER JOIN users

            ON students.user_id=users.id

        INNER JOIN laundromats

            ON bookings.laundromat_id=laundromats.id

        ORDER BY bookings.created_at DESC

        LIMIT 5

    """)
    return jsonify({

        "success": True,

        "statistics":{

            "students":students["total"],

            "laundromats":laundromats["total"],

            "bookings":bookings["total"],

            "revenue":revenue["total"],

            "processing":processing["total"],

            "completed":completed["total"],

            "cancelled":cancelled["total"],

            "successful_payments":successful["total"],

            "pending_payments":pending["total"],

            "refunded_payments":refunded["total"]

        },

        "recent_activity":recent_activity

    })