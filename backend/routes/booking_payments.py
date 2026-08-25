from flask import Blueprint, request, jsonify

from database import (
    fetch_one,
    execute_query
)

import uuid


booking_payments = Blueprint(
    "booking_payments",
    __name__
)


# ============================================================
# CREATE BOOKING + PAYMENT
# ============================================================

@booking_payments.route(
    "/booking-payments",
    methods=["POST"]
)
def create_booking_payment():

    try:

        # ====================================================
        # GET REQUEST DATA
        # ====================================================

        data = request.get_json(
            silent=True
        ) or {}


        booking_data = data.get(
            "booking"
        )


        user_id = data.get(
            "user_id"
        )


        payment_method = data.get(
            "payment_method"
        )


        print(
            "BOOKING PAYMENT DATA:",
            data
        )


        # ====================================================
        # VALIDATE BOOKING
        # ====================================================

        if not booking_data:

            return jsonify({

                "success": False,

                "message":
                    "Booking information is required."

            }), 400


        if not user_id:

            return jsonify({

                "success": False,

                "message":
                    "User ID is required."

            }), 400


        if not payment_method:

            return jsonify({

                "success": False,

                "message":
                    "Payment method is required."

            }), 400


        # ====================================================
        # REQUIRED BOOKING FIELDS
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

            if booking_data.get(field) in [
                None,
                ""
            ]:

                missing.append(
                    field
                )


        if missing:

            return jsonify({

                "success": False,

                "message":
                    "Missing booking fields.",

                "missing":
                    missing

            }), 400


        # ====================================================
        # SECURITY CHECK
        # ====================================================

        if int(
            booking_data["user_id"]
        ) != int(user_id):

            return jsonify({

                "success": False,

                "message":
                    "User mismatch."

            }), 403


        # ====================================================
        # FIND STUDENT
        # ====================================================

        student = fetch_one(
            """
            SELECT id
            FROM students
            WHERE user_id=%s
            """,
            (
                user_id,
            )
        )


        if not student:

            return jsonify({

                "success": False,

                "message":
                    "Student record not found."

            }), 404


        student_id = student["id"]


        # ====================================================
        # VERIFY LAUNDROMAT
        # ====================================================

        laundromat = fetch_one(
            """
            SELECT
                id,
                business_name
            FROM laundromats
            WHERE id=%s
            """,
            (
                booking_data[
                    "laundromat_id"
                ],
            )
        )


        if not laundromat:

            return jsonify({

                "success": False,

                "message":
                    "Laundromat not found."

            }), 404


        # ====================================================
        # VERIFY SERVICE IF service_id WAS PROVIDED
        # ====================================================

        service_id = booking_data.get(
                "service_id"
            )


        if service_id:

            service = fetch_one(
                """
                SELECT
                    id,
                    name,
                    price
                FROM services
                WHERE id=%s
                """,
                (
                    service_id,
                )
            )


            if not service:

                return jsonify({

                    "success": False,

                    "message":
                        "Service not found."

                }), 404


        # ====================================================
        # CALCULATE AMOUNT ON SERVER
        # ====================================================

        amount = float(
            booking_data["amount"]
        )


        if amount <= 0:

            return jsonify({

                "success": False,

                "message":
                    "Invalid booking amount."

            }), 400


        # ====================================================
        # GENERATE BOOKING NUMBER
        # ====================================================

        booking_number = (
            "LC-" +
            uuid.uuid4()
            .hex[:8]
            .upper()
        )


        # ====================================================
        # INSERT BOOKING
        #
        # IMPORTANT:
        # THIS IS THE FIRST TIME THE BOOKING
        # IS CREATED IN THE DATABASE.
        #
        # IT ONLY HAPPENS AFTER PAYMENT REQUEST.
        # ====================================================

        booking_query = """

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


        booking_success = execute_query(

                booking_query,

                (

                    booking_number,

                    student_id,

                    booking_data[
                        "laundromat_id"
                    ],

                    booking_data[
                        "service"
                    ],

                    booking_data[
                        "pickup_date"
                    ],

                    booking_data[
                        "pickup_time"
                    ],

                    booking_data[
                        "loads"
                    ],

                    booking_data[
                        "weight"
                    ],

                    booking_data.get(
                        "instructions",
                        ""
                    ),

                    amount,

                    "Confirmed"

                )

            )


        if not booking_success:

            return jsonify({

                "success": False,

                "message":
                    "Unable to create booking."

            }), 500


        # ====================================================
        # GET NEW BOOKING
        #
        # We retrieve it using booking_number.
        # This avoids relying on execute_query returning
        # the inserted ID.
        # ====================================================

        new_booking = fetch_one(
            """
            SELECT
                id,
                booking_number,
                amount,
                status
            FROM bookings
            WHERE booking_number=%s
            LIMIT 1
            """,
            (
                booking_number,
            )
        )


        if not new_booking:

            return jsonify({

                "success": False,

                "message":
                    "Booking was created but could not be retrieved."

            }), 500


        booking_id = new_booking["id"]


        # ====================================================
        # PREVENT DUPLICATE PAYMENT
        # ====================================================

        existing_payment = fetch_one(
            """
            SELECT id
            FROM payments
            WHERE booking_id=%s
            LIMIT 1
            """,
            (
                booking_id,
            )
        )


        if existing_payment:

            return jsonify({

                "success": False,

                "message":
                    "This booking has already been paid."

            }), 400


        # ====================================================
        # GENERATE TRANSACTION ID
        # ====================================================

        transaction_id = (
            "PAY-" +
            uuid.uuid4()
            .hex[:10]
            .upper()
        )


        # ====================================================
        # CREATE PAYMENT
        # ====================================================

        payment_success = execute_query(
                """

                INSERT INTO payments(

                    booking_id,

                    transaction_id,

                    amount,

                    payment_method,

                    payment_date,

                    payment_status,

                    status

                )

                VALUES(

                    %s,
                    %s,
                    %s,
                    %s,
                    NOW(),
                    %s,
                    %s

                )

                """,
                (

                    booking_id,

                    transaction_id,

                    amount,

                    payment_method,

                    "Paid",

                    "Paid"

                )
            )


        if not payment_success:

            # ------------------------------------------------
            # PAYMENT FAILED
            #
            # Since the booking was just created, remove it.
            # ------------------------------------------------

            execute_query(
                """
                DELETE FROM bookings
                WHERE id=%s
                """,
                (
                    booking_id,
                )
            )


            return jsonify({

                "success": False,

                "message":
                    "Unable to process payment."

            }), 500


        # ====================================================
        # CONFIRM BOOKING
        # ====================================================

        execute_query(
            """

            UPDATE bookings

            SET status=%s

            WHERE id=%s

            """,
            (

                "Confirmed",

                booking_id

            )
        )


        # ====================================================
        # SUCCESS
        # ====================================================

        return jsonify({

            "success": True,

            "message":
                "Payment completed successfully.",

            "booking_id":
                booking_id,

            "booking_number":
                booking_number,

            "transaction_id":
                transaction_id,

            "amount":
                float(amount),

            "status":
                "Confirmed",

            "payment_status":
                "Paid"

        }), 201


    except Exception as error:

        print(
            "BOOKING PAYMENT ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to process booking payment.",

            "error":
                str(error)

        }), 500