from flask import Blueprint, jsonify
from datetime import timedelta, date, datetime
from database import fetch_all, fetch_one, execute_query
from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
orders = Blueprint("orders", __name__)

@orders.route("/orders", methods=["GET"])
def get_orders():

    query = """

        SELECT

            bookings.id,
            bookings.booking_number,
            bookings.service,
            bookings.pickup_date,
            bookings.pickup_time,
            bookings.amount,
            bookings.status,

            CONCAT(
                users.first_name,
                ' ',
                users.last_name
            ) AS student_name,

            users.email AS student_email,

            laundromats.id AS laundromat_id,

            laundromats.business_name

        FROM bookings

        INNER JOIN students
            ON bookings.student_id = students.id

        INNER JOIN users
            ON students.user_id = users.id

        INNER JOIN laundromats
            ON bookings.laundromat_id = laundromats.id

        ORDER BY bookings.created_at DESC

    """

    orders = fetch_all(query)

    # Convert TIME to JSON-safe string
    for order in orders:

        if isinstance(
            order.get("pickup_time"),
            timedelta
        ):

            total_seconds = int(
                order["pickup_time"]
                .total_seconds()
            )

            hours = total_seconds // 3600

            minutes = (
                total_seconds % 3600
            ) // 60

            seconds = (
                total_seconds % 60
            )

            order["pickup_time"] = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )


        if isinstance(
            order.get("pickup_date"),
            date
        ):

            order["pickup_date"] = \
                order["pickup_date"].isoformat()


    return jsonify({

        "success": True,

        "orders": orders

    })
@orders.route("/orders/<int:id>", methods=["GET"])
def get_order(id):

    query = """

    SELECT

        bookings.*,

        CONCAT(
            users.first_name,
            ' ',
            users.last_name
        ) AS student_name,

        users.phone AS student_phone,

        users.email AS student_email,

        laundromats.business_name,

        laundromats.id AS laundromat_id

    FROM bookings

    INNER JOIN students
        ON bookings.student_id = students.id

    INNER JOIN users
        ON students.user_id = users.id

    INNER JOIN laundromats
        ON bookings.laundromat_id = laundromats.id

    WHERE bookings.id=%s

    """

    order = fetch_one(query, (id,))

    if not order:

        return jsonify({

            "success": False,
            "message": "Order not found"

        }), 404


    # ==========================================
    # Convert database values to JSON-safe values
    # ==========================================

    # Convert TIME
    if isinstance(order.get("pickup_time"), timedelta):

        total_seconds = int(
            order["pickup_time"].total_seconds()
        )

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        seconds = (
            total_seconds % 60
        )

        order["pickup_time"] = (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )


    # Convert DATE
    if isinstance(order.get("pickup_date"), date):

        order["pickup_date"] = (
            order["pickup_date"].isoformat()
        )


    # Convert DATETIME
    if isinstance(order.get("created_at"), datetime):

        order["created_at"] = (
            order["created_at"].isoformat()
        )


    # ==========================================
    # Return order
    # ==========================================

    return jsonify({

        "success": True,

        "order": order

    })
@orders.route("/orders/<int:id>/accept", methods=["PUT"])
def accept_order(id):

    success = execute_query(

        """

        UPDATE bookings

        SET status='Accepted'

        WHERE id=%s

        """,

        (id,)

    )

    if success:

        return jsonify({

            "success":True,

            "message":"Order accepted."

        })

    return jsonify({

        "success":False,

        "message":"Unable to accept order."

    }),500
@orders.route("/orders/<int:id>/reject", methods=["PUT"])
def reject_order(id):

    success = execute_query(

        """

        UPDATE bookings

        SET status='Rejected'

        WHERE id=%s

        """,

        (id,)

    )

    if success:

        return jsonify({

            "success":True,

            "message":"Order rejected."

        })

    return jsonify({

        "success":False,

        "message":"Unable to reject order."

    }),500
@orders.route("/orders/<int:id>/processing", methods=["PUT"])
def processing_order(id):

    success = execute_query(

        """

        UPDATE bookings

        SET status='Processing'

        WHERE id=%s

        """,

        (id,)

    )

    if success:

        return jsonify({

            "success":True,

            "message":"Laundry is now being processed."

        })

    return jsonify({

        "success":False,

        "message":"Unable to update order."

    }),500
@orders.route("/orders/<int:id>/ready", methods=["PUT"])
def ready_order(id):

    success = execute_query(

        """

        UPDATE bookings

        SET status='Ready for Collection'

        WHERE id=%s

        """,

        (id,)

    )

    if success:

        return jsonify({

            "success":True,

            "message":"Laundry is ready for collection."

        })

    return jsonify({

        "success":False,

        "message":"Unable to update order."

    }),500
@orders.route("/orders/<int:id>/complete", methods=["PUT"])
def complete_order(id):

    success = execute_query(

        """

        UPDATE bookings

        SET status='Completed'

        WHERE id=%s

        """,

        (id,)

    )

    if success:

        return jsonify({

            "success":True,

            "message":"Order completed."

        })

    return jsonify({

        "success":False,

        "message":"Unable to complete order."

    }),500



@orders.route("/orders/student/<int:user_id>", methods=["GET"])
def get_student_orders(user_id):

    query = """

    SELECT

        bookings.id,
        bookings.booking_number,

        bookings.student_id,

        bookings.laundromat_id,

        laundromats.business_name,

        bookings.service,

        bookings.pickup_date,

        bookings.pickup_time,

        bookings.loads,

        bookings.weight,

        bookings.instructions,

        bookings.amount,

        bookings.status,

        bookings.created_at

    FROM bookings

    INNER JOIN students

        ON bookings.student_id = students.id

    INNER JOIN laundromats

        ON bookings.laundromat_id = laundromats.id

    WHERE students.user_id = %s

    ORDER BY bookings.created_at DESC

    """

    orders = fetch_all(query, (user_id,))


    # Convert MySQL TIME/timedelta values into strings
    for order in orders:

        if order.get("pickup_time") is not None:

            order["pickup_time"] = str(
                order["pickup_time"]
            )


    return jsonify({

        "success": True,

        "orders": orders

    })
@orders.route("/orders/laundromat/<int:laundromat_id>", methods=["GET"])
def get_laundromat_orders(laundromat_id):

    query = """

    SELECT

        bookings.id,
        bookings.booking_number,

        bookings.student_id,
        bookings.laundromat_id,

        CONCAT(
            users.first_name,
            ' ',
            users.last_name
        ) AS student_name,

        users.email AS student_email,
        users.phone AS student_phone,

        laundromats.business_name,

        bookings.service,
        bookings.pickup_date,
        bookings.pickup_time,

        bookings.loads,
        bookings.weight,
        bookings.instructions,

        bookings.amount,
        bookings.status,

        bookings.created_at

    FROM bookings

    INNER JOIN students
        ON bookings.student_id = students.id

    INNER JOIN users
        ON students.user_id = users.id

    INNER JOIN laundromats
        ON bookings.laundromat_id = laundromats.id

    WHERE bookings.laundromat_id = %s

    ORDER BY bookings.created_at DESC

    """

    result = fetch_all(
        query,
        (laundromat_id,)
    )


    # Convert MySQL date/time objects to strings
    for order in result:

        if order.get("pickup_date") is not None:
            order["pickup_date"] = str(
                order["pickup_date"]
            )

        if order.get("pickup_time") is not None:
            order["pickup_time"] = str(
                order["pickup_time"]
            )

        if order.get("created_at") is not None:
            order["created_at"] = str(
                order["created_at"]
            )


    return jsonify({

        "success": True,

        "orders": result

    })

@orders.route("/orders/laundromat/user/<int:user_id>", methods=["GET"])
def get_laundromat_orders_by_user(user_id):

    query = """

        SELECT

            bookings.id,
            bookings.booking_number,

            bookings.service,

            bookings.pickup_date,
            bookings.pickup_time,

            bookings.loads,
            bookings.weight,

            bookings.instructions,

            bookings.amount,

            bookings.status,

            CONCAT(
                users.first_name,
                ' ',
                users.last_name
            ) AS student_name,

            users.phone AS student_phone,

            users.email AS student_email,

            laundromats.id AS laundromat_id,

            laundromats.business_name

        FROM bookings

        INNER JOIN laundromats
            ON bookings.laundromat_id = laundromats.id

        INNER JOIN students
            ON bookings.student_id = students.id

        INNER JOIN users
            ON students.user_id = users.id

        WHERE laundromats.user_id = %s

        ORDER BY bookings.created_at DESC

    """

    orders = fetch_all(
        query,
        (user_id,)
    )


    # Convert database values into JSON-safe values
    for order in orders:

        # Convert TIME
        if isinstance(order.get("pickup_time"), timedelta):

            total_seconds = int(
                order["pickup_time"].total_seconds()
            )

            hours = total_seconds // 3600

            minutes = (
                total_seconds % 3600
            ) // 60

            seconds = (
                total_seconds % 60
            )

            order["pickup_time"] = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )


        # Convert DATE
        if isinstance(order.get("pickup_date"), date):

            order["pickup_date"] = (
                order["pickup_date"].isoformat()
            )


        # Convert datetime values if any
        if isinstance(order.get("created_at"), datetime):

            order["created_at"] = (
                order["created_at"].isoformat()
            )


    return jsonify({

        "success": True,

        "orders": orders

    })

@orders.route("/reports/laundromat/<int:user_id>", methods=["GET"])
def get_laundromat_report(user_id):

    query = """

        SELECT

            bookings.id,
            bookings.booking_number,
            bookings.service,
            bookings.pickup_date,
            bookings.pickup_time,
            bookings.amount,
            bookings.status,

            CONCAT(
                users.first_name,
                ' ',
                users.last_name
            ) AS student_name,

            laundromats.id AS laundromat_id,
            laundromats.business_name

        FROM bookings

        INNER JOIN laundromats
            ON bookings.laundromat_id = laundromats.id

        INNER JOIN students
            ON bookings.student_id = students.id

        INNER JOIN users
            ON students.user_id = users.id

        WHERE laundromats.user_id = %s

        ORDER BY bookings.created_at DESC

    """

    reports = fetch_all(
        query,
        (user_id,)
    )

    # Convert database values to JSON-safe values
    for report in reports:

        # TIME
        if isinstance(report.get("pickup_time"), timedelta):

            total_seconds = int(
                report["pickup_time"].total_seconds()
            )

            hours = total_seconds // 3600

            minutes = (
                total_seconds % 3600
            ) // 60

            seconds = (
                total_seconds % 60
            )

            report["pickup_time"] = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        # DATE
        if isinstance(report.get("pickup_date"), date):

            report["pickup_date"] = \
                report["pickup_date"].isoformat()

        # DATETIME
        if isinstance(report.get("created_at"), datetime):

            report["created_at"] = \
                report["created_at"].isoformat()

    return jsonify({

        "success": True,

        "reports": reports

    })
@orders.route("/orders/<int:booking_id>", methods=["PUT"])
def update_order_status(booking_id):

    data = request.get_json()

    print("UPDATE DATA:", data)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    status = data.get("status")

    estimated_completion = data.get(
        "estimated_completion"
    )

    staff_notes = data.get(
        "staff_notes"
    )

    valid_statuses = [
        "Pending",
        "Confirmed",
        "Processing",
        "Washing",
        "Drying",
        "Ready for Pickup",
        "Completed",
        "Cancelled"
    ]

    # ==========================================
    # CHECK VALID STATUS
    # ==========================================

    if status not in valid_statuses:

        return jsonify({
            "success": False,
            "message": "Please select a valid status."
        }), 400


    # ==========================================
    # GET CURRENT ORDER
    # ==========================================

    existing_order = fetch_one(
        """
        SELECT
            id,
            status
        FROM bookings
        WHERE id = %s
        """,
        (booking_id,)
    )


    if not existing_order:

        return jsonify({
            "success": False,
            "message": "Booking not found."
        }), 404


    current_status = existing_order["status"]


    # ==========================================
    # CANCELLED ORDERS ARE LOCKED
    # ==========================================

    if current_status == "Cancelled":

        return jsonify({
            "success": False,
            "locked": True,
            "message":
                "This booking has been cancelled and can no longer be updated."
        }), 403


    # ==========================================
    # COMPLETED ORDERS ARE ALSO LOCKED
    # ==========================================

    if current_status == "Completed":

        return jsonify({
            "success": False,
            "locked": True,
            "message":
                "This booking has already been completed and can no longer be updated."
        }), 403


    # ==========================================
    # PREVENT CHANGING TO CANCELLED
    # AFTER COMPLETION
    # ==========================================

    if current_status == "Completed" and status == "Cancelled":

        return jsonify({
            "success": False,
            "locked": True,
            "message":
                "A completed booking cannot be cancelled."
        }), 403


    # ==========================================
    # UPDATE STATUS
    # ==========================================

    query = """
        UPDATE bookings

        SET
            status = %s,
            estimated_completion = %s,
            staff_notes = %s

        WHERE id = %s
    """


    success = execute_query(
        query,
        (
            status,
            estimated_completion,
            staff_notes,
            booking_id
        )
    )


    if not success:

        return jsonify({
            "success": False,
            "message": "Failed to update booking."
        }), 500


    return jsonify({
        "success": True,
        "message": "Booking status updated successfully."
    })


@orders.route("/orders/<int:id>/cancel", methods=["PUT"])
def cancel_order(id):

    # ==========================================
    # GET CURRENT BOOKING
    # ==========================================

    order = fetch_one(
        """
        SELECT
            id,
            status
        FROM bookings
        WHERE id = %s
        """,
        (id,)
    )


    if not order:

        return jsonify({
            "success": False,
            "message": "Booking not found."
        }), 404


    current_status = order["status"]


    # ==========================================
    # PREVENT CANCELLING COMPLETED ORDER
    # ==========================================

    if current_status == "Completed":

        return jsonify({
            "success": False,
            "message":
                "Completed bookings cannot be cancelled."
        }), 403


    # ==========================================
    # PREVENT CANCELLING ALREADY CANCELLED ORDER
    # ==========================================

    if current_status == "Cancelled":

        return jsonify({
            "success": False,
            "message":
                "This booking has already been cancelled."
        }), 403


    # ==========================================
    # CANCEL BOOKING
    # ==========================================

    success = execute_query(
        """
        UPDATE bookings

        SET status = 'Cancelled'

        WHERE id = %s
        """,
        (id,)
    )


    if success:

        return jsonify({
            "success": True,
            "message":
                "Booking cancelled successfully."
        })


    return jsonify({
        "success": False,
        "message":
            "Unable to cancel booking."
    }), 500