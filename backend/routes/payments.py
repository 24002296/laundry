from flask import Blueprint, request, jsonify
from database import fetch_all, fetch_one, execute_query

from datetime import datetime, date, time, timedelta
from decimal import Decimal


payments = Blueprint("payments", __name__)


# ============================================================
# JSON SERIALIZER
# ============================================================

def serialize_value(value):

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return value


def serialize_row(row):

    if row is None:
        return None

    return {
        key: serialize_value(value)
        for key, value in row.items()
    }


# ============================================================
# GET ALL PAYMENTS
# ============================================================

@payments.route("/payments", methods=["GET"])
def get_payments():

    try:

        query = """
            SELECT

                payments.id,
                payments.transaction_id,

                bookings.booking_number,

                CONCAT(
                    student.first_name,
                    ' ',
                    student.last_name
                ) AS student,

                laundromats.business_name
                AS laundromat,

                payments.amount,
                payments.payment_method,
                payments.payment_date,
                payments.status

            FROM payments

            INNER JOIN bookings
                ON payments.booking_id = bookings.id

            INNER JOIN students
                ON bookings.student_id = students.id

            INNER JOIN users AS student
                ON students.user_id = student.id

            INNER JOIN laundromats
                ON bookings.laundromat_id = laundromats.id

            ORDER BY payments.payment_date DESC
        """

        result = fetch_all(query)

        payments_list = [
            serialize_row(payment)
            for payment in result
        ]

        return jsonify({

            "success": True,
            "payments": payments_list

        })

    except Exception as error:

        print("GET PAYMENTS ERROR:", error)

        return jsonify({

            "success": False,
            "message": "Unable to load payments.",
            "error": str(error)

        }), 500


# ============================================================
# GET ONE PAYMENT
# ============================================================

@payments.route("/payments/<int:id>", methods=["GET"])
def get_payment(id):

    try:

        query = """
            SELECT *

            FROM payments

            WHERE id = %s
        """

        payment = fetch_one(
            query,
            (id,)
        )

        if not payment:

            return jsonify({

                "success": False,
                "message": "Payment not found."

            }), 404

        return jsonify({

            "success": True,
            "payment": serialize_row(payment)

        })

    except Exception as error:

        print("GET PAYMENT ERROR:", error)

        return jsonify({

            "success": False,
            "message": "Unable to load payment.",
            "error": str(error)

        }), 500


# ============================================================
# CREATE PAYMENT
# ============================================================

@payments.route("/payments", methods=["POST"])
def create_payment():

    try:

        data = request.get_json(silent=True) or {}

        booking_id = data.get("booking_id")
        amount = data.get("amount")
        payment_method = data.get("payment_method")

        if not booking_id:
            return jsonify({

                "success": False,
                "message": "Booking ID is required."

            }), 400

        if amount in [None, ""]:
            return jsonify({

                "success": False,
                "message": "Payment amount is required."

            }), 400

        if not payment_method:
            return jsonify({

                "success": False,
                "message": "Payment method is required."

            }), 400


        # Check booking exists

        booking = fetch_one(
            """
            SELECT id
            FROM bookings
            WHERE id = %s
            """,
            (booking_id,)
        )

        if not booking:

            return jsonify({

                "success": False,
                "message": "Booking not found."

            }), 404


        # Generate transaction ID

        import uuid

        transaction_id = (
            "TXN-"
            + uuid.uuid4().hex[:10].upper()
        )


        query = """

            INSERT INTO payments(

                booking_id,
                transaction_id,
                amount,
                payment_method,
                payment_date,
                status

            )

            VALUES(

                %s,
                %s,
                %s,
                %s,
                NOW(),
                %s

            )

        """


        success = execute_query(

            query,

            (
                booking_id,
                transaction_id,
                amount,
                payment_method,
                "Paid"
            )

        )


        if success:

            return jsonify({

                "success": True,
                "message":
                    "Payment completed successfully.",
                "transaction_id":
                    transaction_id

            }), 201


        return jsonify({

            "success": False,
            "message": "Payment failed."

        }), 500


    except Exception as error:

        print("CREATE PAYMENT ERROR:", error)

        return jsonify({

            "success": False,
            "message": "Unable to create payment.",
            "error": str(error)

        }), 500


# ============================================================
# UPDATE PAYMENT
# ============================================================

@payments.route("/payments/<int:id>", methods=["PUT"])
def update_payment(id):

    try:

        data = request.get_json(silent=True) or {}

        status = data.get("status")

        if not status:

            return jsonify({

                "success": False,
                "message": "Payment status is required."

            }), 400


        query = """

            UPDATE payments

            SET status = %s

            WHERE id = %s

        """


        success = execute_query(

            query,

            (
                status,
                id
            )

        )


        if success:

            return jsonify({

                "success": True,
                "message": "Payment updated successfully."

            })


        return jsonify({

            "success": False,
            "message": "Unable to update payment."

        }), 500


    except Exception as error:

        print("UPDATE PAYMENT ERROR:", error)

        return jsonify({

            "success": False,
            "message": "Unable to update payment.",
            "error": str(error)

        }), 500


# ============================================================
# DELETE PAYMENT
# ============================================================

@payments.route("/payments/<int:id>", methods=["DELETE"])
def delete_payment(id):

    try:

        success = execute_query(

            """
            DELETE FROM payments
            WHERE id = %s
            """,

            (id,)

        )


        if success:

            return jsonify({

                "success": True,
                "message": "Payment deleted successfully."

            })


        return jsonify({

            "success": False,
            "message": "Unable to delete payment."

        }), 500


    except Exception as error:

        print("DELETE PAYMENT ERROR:", error)

        return jsonify({

            "success": False,
            "message": "Unable to delete payment.",
            "error": str(error)

        }), 500


# ============================================================
# SEARCH PAYMENTS
# ============================================================

@payments.route(
    "/payments/search/<string:keyword>",
    methods=["GET"]
)
def search_payment(keyword):

    try:

        search = "%" + keyword + "%"


        query = """

            SELECT

                payments.id,
                payments.transaction_id,

                bookings.booking_number,

                CONCAT(
                    student.first_name,
                    ' ',
                    student.last_name
                ) AS student,

                laundromats.business_name
                AS laundromat,

                payments.amount,
                payments.payment_method,
                payments.payment_date,
                payments.status

            FROM payments

            INNER JOIN bookings
                ON payments.booking_id = bookings.id

            INNER JOIN students
                ON bookings.student_id = students.id

            INNER JOIN users AS student
                ON students.user_id = student.id

            INNER JOIN laundromats
                ON bookings.laundromat_id = laundromats.id

            WHERE

                payments.transaction_id LIKE %s

                OR student.first_name LIKE %s

                OR student.last_name LIKE %s

                OR laundromats.business_name LIKE %s

            ORDER BY payments.payment_date DESC

        """


        result = fetch_all(

            query,

            (
                search,
                search,
                search,
                search
            )

        )


        payments_list = [
            serialize_row(payment)
            for payment in result
        ]


        return jsonify({

            "success": True,
            "payments": payments_list

        })


    except Exception as error:

        print("SEARCH PAYMENTS ERROR:", error)

        return jsonify({

            "success": False,
            "message": "Unable to search payments.",
            "error": str(error)

        }), 500