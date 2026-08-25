from flask import Blueprint, request, jsonify
from database import fetch_all, fetch_one, execute_query

from sms_service import send_sms
from datetime import timedelta, datetime, date, time
import uuid


bookings = Blueprint("bookings", __name__)


# ============================================================
# SERIALIZE DATABASE VALUES
# ============================================================

def serialize_value(value):

    # MySQL TIME may come back as timedelta
    if isinstance(value, timedelta):

        total_seconds = int(value.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Python time object
    if isinstance(value, time):

        return value.strftime("%H:%M:%S")

    # Python datetime
    if isinstance(value, datetime):

        return value.strftime("%Y-%m-%d %H:%M:%S")

    # Python date
    if isinstance(value, date):

        return value.strftime("%Y-%m-%d")

    return value


def serialize_row(row):

    if not row:
        return row

    return {
        key: serialize_value(value)
        for key, value in row.items()
    }


def serialize_rows(rows):

    return [
        serialize_row(row)
        for row in (rows or [])
    ]
@bookings.route("/bookings", methods=["GET"])
def get_bookings():

    query = """

        SELECT

            bookings.id,
            bookings.booking_number,

            CONCAT(
                student.first_name,
                ' ',
                student.last_name
            ) AS student,

            laundromats.business_name AS laundromat,

            bookings.service,
            bookings.pickup_date,
            bookings.pickup_time,
            bookings.loads,
            bookings.weight,
            bookings.amount,
            bookings.status,
            bookings.created_at

        FROM bookings

        INNER JOIN students
            ON bookings.student_id = students.id

        INNER JOIN users AS student
            ON students.user_id = student.id

        INNER JOIN laundromats
            ON bookings.laundromat_id = laundromats.id

        ORDER BY bookings.created_at DESC

    """

    result = fetch_all(query)

    # IMPORTANT:
    # Convert timedelta/date/time/datetime
    # into JSON-compatible values.
    result = serialize_rows(result)

    return jsonify({

        "success": True,
        "bookings": result

    })
@bookings.route("/bookings/<int:id>", methods=["GET"])
def get_booking(id):

    try:

        query = """

            SELECT

                bookings.*,

                CONCAT(
                    student.first_name,
                    ' ',
                    student.last_name
                ) AS student,

                laundromats.business_name AS laundromat

            FROM bookings

            INNER JOIN students
                ON bookings.student_id = students.id

            INNER JOIN users AS student
                ON students.user_id = student.id

            INNER JOIN laundromats
                ON bookings.laundromat_id = laundromats.id

            WHERE bookings.id = %s

        """

        booking = fetch_one(
            query,
            (id,)
        )

        if not booking:

            return jsonify({

                "success": False,

                "message": "Booking not found."

            }), 404


        booking = serialize_row(booking)


        return jsonify({

            "success": True,

            "booking": booking

        })


    except Exception as error:

        print(
            "GET BOOKING ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to load booking.",

            "error":
                str(error)

        }), 500
@bookings.route(
    "/bookings",
    methods=["POST"]
)
def create_booking():

    try:

        data = request.get_json(
            silent=True
        )

        print(
            "BOOKING DATA RECEIVED:",
            data
        )


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No booking data received."

            }), 400


        # ====================================================
        # REQUIRED FIELDS
        # ====================================================

        required_fields = [

            "user_id",
            "laundromat_id",
            "service",
            "pickup_date",
            "pickup_time",
            "loads",
            "weight",
            "amount"

        ]


        missing = []


        for field in required_fields:

            if data.get(field) in [
                None,
                ""
            ]:

                missing.append(field)


        if missing:

            return jsonify({

                "success": False,

                "message":
                    "Missing required fields.",

                "missing":
                    missing

            }), 400


        # ====================================================
        # FIND STUDENT
        # ====================================================

        student = fetch_one(

            """
            SELECT
                students.id,
                users.first_name,
                users.last_name,
                users.phone

            FROM students

            INNER JOIN users
                ON students.user_id = users.id

            WHERE students.user_id = %s

            LIMIT 1
            """,

            (data["user_id"],)

        )


        if not student:

            return jsonify({

                "success": False,

                "message":
                    "Student record not found."

            }), 404


        student_id = student["id"]


        # ====================================================
        # FIND LAUNDROMAT
        # ====================================================

        laundromat = fetch_one(

            """
            SELECT

                id,
                user_id,
                business_name

            FROM laundromats

            WHERE id = %s

            LIMIT 1
            """,

            (data["laundromat_id"],)

        )


        if not laundromat:

            return jsonify({

                "success": False,

                "message":
                    "Laundromat not found."

            }), 404


        # ====================================================
        # FIND LAUNDROMAT OWNER PHONE
        # ====================================================

        laundromat_owner = fetch_one(

            """
            SELECT

                id,
                first_name,
                last_name,
                phone

            FROM users

            WHERE id = %s

            LIMIT 1
            """,

            (laundromat["user_id"],)

        )


        if not laundromat_owner:

            return jsonify({

                "success": False,

                "message":
                    "Laundromat owner account not found."

            }), 404


        # ====================================================
        # GENERATE BOOKING NUMBER
        # ====================================================

        booking_number = (

            "LC-" +
            uuid.uuid4().hex[:8].upper()

        )


        # ====================================================
        # INSERT BOOKING
        # ====================================================

        query = """

            INSERT INTO bookings(

                booking_number,
                student_id,
                laundromat_id,
                service,
                pickup_date,
                pickup_time,
                loads,
                weight,
                instructions,
                amount,
                status

            )

            VALUES(

                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
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

                booking_number,

                student_id,

                data["laundromat_id"],

                data["service"],

                data["pickup_date"],

                data["pickup_time"],

                data["loads"],

                data["weight"],

                data.get(
                    "instructions",
                    ""
                ),

                data["amount"],

                data.get(
                    "status",
                    "Pending"
                )

            )

        )


        if not success:

            return jsonify({

                "success": False,

                "message":
                    "Unable to create booking."

            }), 500


        # ====================================================
        # GET NEW BOOKING
        # ====================================================

        new_booking = fetch_one(

            """
            SELECT

                id,
                booking_number,
                amount,
                status

            FROM bookings

            WHERE booking_number = %s

            LIMIT 1

            """,

            (booking_number,)

        )


        if not new_booking:

            return jsonify({

                "success": False,

                "message":
                    "Booking was created but could not be retrieved."

            }), 500


        # ====================================================
        # SEND SMS TO LAUNDROMAT
        # ====================================================

        send_sms(

            laundromat_owner["phone"],

            (
                f"Campus Laundry Connect: "
                f"New booking received. "
                f"Booking: {booking_number}. "
                f"Student: "
                f"{student['first_name']} "
                f"{student['last_name']}. "
                f"Service: {data['service']}. "
                f"Status: {new_booking['status']}."
            )

        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "message":
                "Booking created successfully.",

            "booking_id":
                new_booking["id"],

            "booking_number":
                new_booking["booking_number"],

            "amount":
                float(
                    new_booking["amount"]
                ),

            "status":
                new_booking["status"]

        }), 201


    except Exception as error:

        print(
            "CREATE BOOKING ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to create booking.",

            "error":
                str(error)

        }), 500
@bookings.route(
    "/bookings/<int:id>",
    methods=["PUT"]
)
def update_booking(id):

    try:

        data = request.get_json(
            silent=True
        ) or {}


        new_status = data.get(
            "status"
        )


        if not new_status:

            return jsonify({

                "success": False,

                "message":
                    "Booking status is required."

            }), 400


        # ====================================================
        # GET BOOKING + STUDENT PHONE
        # ====================================================

        booking = fetch_one(

            """
            SELECT

                bookings.id,
                bookings.booking_number,
                bookings.status,

                student.first_name,
                student.last_name,
                student.phone

            FROM bookings

            INNER JOIN students
                ON bookings.student_id = students.id

            INNER JOIN users AS student
                ON students.user_id = student.id

            WHERE bookings.id = %s

            LIMIT 1

            """,

            (id,)

        )


        if not booking:

            return jsonify({

                "success": False,

                "message":
                    "Booking not found."

            }), 404


        old_status = booking["status"]


        # ====================================================
        # UPDATE
        # ====================================================

        success = execute_query(

            """
            UPDATE bookings

            SET status = %s

            WHERE id = %s
            """,

            (
                new_status,
                id
            )

        )


        if not success:

            return jsonify({

                "success": False,

                "message":
                    "Unable to update booking."

            }), 500


        # ====================================================
        # SEND SMS ONLY IF STATUS CHANGED
        # ====================================================

        if old_status != new_status:

            send_sms(

                booking["phone"],

                (
                    f"Campus Laundry Connect: "
                    f"Your booking "
                    f"{booking['booking_number']} "
                    f"status has changed from "
                    f"{old_status} to "
                    f"{new_status}."
                )

            )


        return jsonify({

            "success": True,

            "message":
                "Booking updated successfully.",

            "status":
                new_status

        })


    except Exception as error:

        print(
            "UPDATE BOOKING ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to update booking.",

            "error":
                str(error)

        }), 500
@bookings.route("/bookings/<int:id>", methods=["DELETE"])
def delete_booking(id):

    try:

        booking = fetch_one(
            """
            SELECT id
            FROM bookings
            WHERE id = %s
            """,
            (id,)
        )

        if not booking:

            return jsonify({

                "success": False,

                "message":
                    "Booking not found."

            }), 404


        execute_query(

            """
            DELETE FROM bookings
            WHERE id = %s
            """,

            (id,)

        )


        return jsonify({

            "success": True,

            "message":
                "Booking deleted successfully."

        })


    except Exception as error:

        print(
            "DELETE BOOKING ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to delete booking.",

            "error":
                str(error)

        }), 500
@bookings.route("/bookings/search/<string:keyword>", methods=["GET"])
def search_booking(keyword):

    search = "%" + keyword + "%"

    query = """

    SELECT

        bookings.id,
        bookings.booking_number,

        CONCAT(student.first_name,' ',student.last_name)
        AS student,

        laundromats.business_name
        AS laundromat,

        bookings.service,
        bookings.status

    FROM bookings

    INNER JOIN students

        ON bookings.student_id=students.id

    INNER JOIN users AS student

        ON students.user_id=student.id

    INNER JOIN laundromats

        ON bookings.laundromat_id=laundromats.id

    WHERE

        bookings.booking_number LIKE %s

        OR

        student.first_name LIKE %s

        OR

        student.last_name LIKE %s

        OR

        laundromats.business_name LIKE %s

    """

    result = fetch_all(

        query,

        (search,search,search,search)

    )

    return jsonify({

        "success":True,
        "bookings":result

    })