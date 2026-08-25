from flask import Blueprint, request, jsonify

from database import fetch_all, fetch_one, execute_query


reviews = Blueprint("reviews", __name__)


# ============================================================
# GET REVIEWS FOR A LAUNDROMAT
# ============================================================

@reviews.route(
    "/reviews/<int:laundromat_id>",
    methods=["GET"]
)
def get_reviews(laundromat_id):

    try:

        query = """
        
        SELECT

            reviews.id,

            reviews.student_id,

            users.id AS user_id,

            reviews.laundromat_id,

            reviews.booking_id,

            reviews.rating,

            reviews.comment,

            reviews.created_at,

            CONCAT(
                users.first_name,
                ' ',
                users.last_name
            ) AS student

            FROM reviews

            INNER JOIN students
                ON reviews.student_id = students.id

            INNER JOIN users
                ON students.user_id = users.id

            WHERE reviews.laundromat_id = %s

            ORDER BY reviews.created_at DESC
        """

        result = fetch_all(
            query,
            (laundromat_id,)
        )


        # ====================================================
        # CALCULATE AVERAGE RATING
        # ====================================================

        rating_query = """

            SELECT

                ROUND(
                    AVG(rating),
                    1
                ) AS average_rating,

                COUNT(*) AS review_count

            FROM reviews

            WHERE laundromat_id = %s

        """

        rating_data = fetch_one(
            rating_query,
            (laundromat_id,)
        )


        average_rating = 0

        review_count = 0


        if rating_data:

            average_rating = float(
                rating_data["average_rating"] or 0
            )

            review_count = int(
                rating_data["review_count"] or 0
            )


        return jsonify({

            "success": True,

            "reviews":
                result or [],

            "average_rating":
                average_rating,

            "review_count":
                review_count

        })


    except Exception as error:

        print(
            "GET REVIEWS ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to load reviews.",

            "error":
                str(error)

        }), 500

# ============================================================
# CHECK WHETHER STUDENT CAN REVIEW
# ============================================================

@reviews.route(
    "/reviews/can-review/<int:user_id>/<int:laundromat_id>",
    methods=["GET"]
)
def can_review(user_id, laundromat_id):

    try:

        # Find student
        student = fetch_one(
            """
            SELECT id
            FROM students
            WHERE user_id = %s
            """,
            (user_id,)
        )

        if not student:

            return jsonify({
                "success": False,
                "can_review": False,
                "message": "Student not found."
            }), 404

        student_id = student["id"]


        # Find a completed booking
        # that has not already been reviewed.

        booking = fetch_one(
            """
            SELECT

                bookings.id,
                bookings.booking_number

            FROM bookings

            LEFT JOIN reviews
                ON reviews.booking_id = bookings.id

            WHERE bookings.student_id = %s

            AND bookings.laundromat_id = %s

            AND bookings.status = 'Completed'

            AND reviews.id IS NULL

            ORDER BY bookings.created_at DESC

            LIMIT 1
            """,
            (
                student_id,
                laundromat_id
            )
        )


        if not booking:

            return jsonify({
                "success": True,
                "can_review": False,
                "message":
                    "You need a completed booking before reviewing this laundromat."
            })


        return jsonify({

            "success": True,

            "can_review": True,

            "booking_id":
                booking["id"],

            "booking_number":
                booking["booking_number"]

        })


    except Exception as error:

        print(
            "CAN REVIEW ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "can_review": False,

            "message":
                "Unable to check review eligibility.",

            "error":
                str(error)

        }), 500


# ============================================================
# CREATE REVIEW
# ============================================================

@reviews.route(
    "/reviews",
    methods=["POST"]
)
def create_review():

    try:

        data = request.get_json(silent=True)


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No review data received."

            }), 400


        required = [

            "user_id",
            "laundromat_id",
            "booking_id",
            "rating"

        ]


        missing = []

        for field in required:

            if data.get(field) in [None, ""]:

                missing.append(field)


        if missing:

            return jsonify({

                "success": False,

                "message":
                    "Missing required fields.",

                "missing":
                    missing

            }), 400


        user_id = int(
            data["user_id"]
        )

        laundromat_id = int(
            data["laundromat_id"]
        )

        booking_id = int(
            data["booking_id"]
        )

        rating = int(
            data["rating"]
        )

        comment = (
            data.get("comment") or ""
        ).strip()


        # ====================================================
        # VALIDATE RATING
        # ====================================================

        if rating < 1 or rating > 5:

            return jsonify({

                "success": False,

                "message":
                    "Rating must be between 1 and 5."

            }), 400


        # ====================================================
        # FIND STUDENT
        # ====================================================

        student = fetch_one(

            """
            SELECT id

            FROM students

            WHERE user_id = %s
            """,

            (user_id,)

        )


        if not student:

            return jsonify({

                "success": False,

                "message":
                    "Student record not found."

            }), 404


        student_id = student["id"]


        # ====================================================
        # VERIFY BOOKING
        # ====================================================

        booking = fetch_one(

            """
            SELECT

                id,
                student_id,
                laundromat_id,
                status

            FROM bookings

            WHERE id = %s

            LIMIT 1
            """,

            (booking_id,)

        )


        if not booking:

            return jsonify({

                "success": False,

                "message":
                    "Booking not found."

            }), 404


        # ====================================================
        # SECURITY CHECK
        # ====================================================

        if booking["student_id"] != student_id:

            return jsonify({

                "success": False,

                "message":
                    "This booking does not belong to you."

            }), 403


        if booking["laundromat_id"] != laundromat_id:

            return jsonify({

                "success": False,

                "message":
                    "Booking does not belong to this laundromat."

            }), 400


        # ====================================================
        # ONLY COMPLETED BOOKINGS CAN BE REVIEWED
        # ====================================================

        if str(
            booking["status"]
        ).lower() != "completed":

            return jsonify({

                "success": False,

                "message":
                    "You can only review a completed booking."

            }), 400


        # ====================================================
        # CHECK EXISTING REVIEW
        # ====================================================

        existing = fetch_one(

            """
            SELECT id

            FROM reviews

            WHERE booking_id = %s

            LIMIT 1
            """,

            (booking_id,)

        )


        if existing:

            return jsonify({

                "success": False,

                "message":
                    "You have already reviewed this booking."

            }), 409


        # ====================================================
        # INSERT REVIEW
        # ====================================================

        success = execute_query(

            """
            INSERT INTO reviews
            (
                student_id,
                laundromat_id,
                booking_id,
                rating,
                comment
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,

            (
                student_id,
                laundromat_id,
                booking_id,
                rating,
                comment
            )

        )


        if not success:

            return jsonify({

                "success": False,

                "message":
                    "Unable to create review."

            }), 500


        # ====================================================
        # RECALCULATE LAUNDROMAT RATING
        # ====================================================

        rating_result = fetch_one(

            """
            SELECT

                ROUND(
                    AVG(rating),
                    1
                ) AS average_rating

            FROM reviews

            WHERE laundromat_id = %s
            """,

            (laundromat_id,)

        )


        average_rating = (
            rating_result["average_rating"]
            if rating_result
            else 0
        )


        execute_query(

            """
            UPDATE laundromats

            SET rating = %s

            WHERE id = %s
            """,

            (
                average_rating,
                laundromat_id
            )

        )


        return jsonify({

            "success": True,

            "message":
                "Review submitted successfully.",

            "rating":
                float(average_rating)

        }), 201


    except Exception as error:

        print(
            "CREATE REVIEW ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to submit review.",

            "error":
                str(error)

        }), 500


# ============================================================
# DELETE REVIEW
# ============================================================

@reviews.route(
    "/reviews/<int:review_id>",
    methods=["DELETE"]
)
def delete_review(review_id):

    try:

        data = request.get_json(silent=True) or {}

        user_id = data.get("user_id")

        if not user_id:

            return jsonify({
                "success": False,
                "message": "User ID is required."
            }), 400


        # ====================================================
        # FIND STUDENT
        # ====================================================

        student = fetch_one(
            """
            SELECT id
            FROM students
            WHERE user_id = %s
            """,
            (user_id,)
        )

        if not student:

            return jsonify({
                "success": False,
                "message": "Student not found."
            }), 404


        student_id = student["id"]


        # ====================================================
        # FIND REVIEW
        # ====================================================

        review = fetch_one(
            """
            SELECT
                id,
                student_id,
                laundromat_id
            FROM reviews
            WHERE id = %s
            LIMIT 1
            """,
            (review_id,)
        )


        if not review:

            return jsonify({
                "success": False,
                "message": "Review not found."
            }), 404


        # ====================================================
        # SECURITY CHECK
        # ====================================================

        if review["student_id"] != student_id:

            return jsonify({
                "success": False,
                "message":
                    "You can only delete your own review."
            }), 403


        laundromat_id = review["laundromat_id"]


        # ====================================================
        # DELETE REVIEW
        # ====================================================

        success = execute_query(
            """
            DELETE FROM reviews
            WHERE id = %s
            """,
            (review_id,)
        )


        if not success:

            return jsonify({
                "success": False,
                "message": "Unable to delete review."
            }), 500


        # ====================================================
        # RECALCULATE LAUNDROMAT RATING
        # ====================================================

        rating_result = fetch_one(
            """
            SELECT
                ROUND(AVG(rating), 1) AS average_rating
            FROM reviews
            WHERE laundromat_id = %s
            """,
            (laundromat_id,)
        )


        average_rating = 0

        if rating_result:

            average_rating = float(
                rating_result["average_rating"] or 0
            )


        # ====================================================
        # UPDATE LAUNDROMAT RATING
        # ====================================================

        execute_query(
            """
            UPDATE laundromats
            SET rating = %s
            WHERE id = %s
            """,
            (
                average_rating,
                laundromat_id
            )
        )


        return jsonify({

            "success": True,

            "message":
                "Review deleted successfully.",

            "rating":
                average_rating

        })


    except Exception as error:

        print(
            "DELETE REVIEW ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to delete review.",

            "error":
                str(error)

        }), 500