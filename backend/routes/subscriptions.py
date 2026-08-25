from flask import Blueprint, request, jsonify

from database import fetch_one, execute_query

from datetime import datetime, timedelta

import uuid


subscriptions = Blueprint(
    "subscriptions",
    __name__
)


@subscriptions.route(
    "/subscriptions",
    methods=["POST"]
)
@subscriptions.route("/subscriptions", methods=["POST"])
def create_subscription():

    try:

        data = request.get_json(silent=True) or {}

        user_id = data.get("user_id")
        role = str(data.get("role", "")).lower()
        plan = data.get("plan")
        amount = data.get("amount")
        payment_method = data.get("payment_method")


        # ==========================================
        # VALIDATION
        # ==========================================

        if not user_id:
            return jsonify({
                "success": False,
                "message": "User ID is required."
            }), 400


        if role not in ["student", "laundromat"]:
            return jsonify({
                "success": False,
                "message": "Invalid user role."
            }), 400


        if not plan:
            return jsonify({
                "success": False,
                "message": "Subscription plan is required."
            }), 400


        if amount is None:
            return jsonify({
                "success": False,
                "message": "Subscription amount is required."
            }), 400


        if not payment_method:
            return jsonify({
                "success": False,
                "message": "Payment method is required."
            }), 400


        # ==========================================
        # CHECK USER EXISTS
        # ==========================================

        user = fetch_one(
            """
            SELECT id, role
            FROM users
            WHERE id=%s
            LIMIT 1
            """,
            (user_id,)
        )


        if not user:

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404


        # ==========================================
        # CHECK EXISTING ACTIVE SUBSCRIPTION
        # ==========================================

        existing = fetch_one(
            """
            SELECT id
            FROM subscriptions
            WHERE user_id=%s
            AND status='Active'
            AND end_date >= NOW()
            LIMIT 1
            """,
            (user_id,)
        )


        if existing:

            return jsonify({
                "success": False,
                "message": "You already have an active subscription."
            }), 409


        # ==========================================
        # TRANSACTION
        # ==========================================

        transaction_id = (
            "SUB-" +
            uuid.uuid4().hex[:10].upper()
        )


        start_date = datetime.now()

        end_date = (
            start_date +
            timedelta(days=30)
        )


        # ==========================================
        # INSERT
        # ==========================================

        query = """
            INSERT INTO subscriptions
            (
                user_id,
                user_role,
                plan,
                amount,
                payment_method,
                transaction_id,
                status,
                start_date,
                end_date
            )

            VALUES
            (
                %s,%s,%s,%s,%s,%s,
                'Active',
                %s,%s
            )
        """


        success = execute_query(
            query,
            (
                user_id,
                role,
                plan,
                amount,
                payment_method,
                transaction_id,
                start_date,
                end_date
            )
        )


        if not success:

            return jsonify({
                "success": False,
                "message":
                    "Unable to activate subscription."
            }), 500


        return jsonify({

            "success": True,

            "message":
                "Subscription activated successfully.",

            "transaction_id":
                transaction_id,

            "plan":
                plan,

            "amount":
                amount,

            "status":
                "Active",

            "end_date":
                end_date.strftime("%Y-%m-%d")

        }), 201


    except Exception as error:

        print(
            "SUBSCRIPTION ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Subscription processing failed.",

            "error":
                str(error)

        }), 500
@subscriptions.route(
    "/subscriptions/user/<int:user_id>",
    methods=["GET"]
)
def get_user_subscription(user_id):

    subscription = fetch_one("""

        SELECT

            id,
            user_id,
            user_role,
            plan,
            amount,
            transaction_id,
            payment_method,
            status,
            start_date,
            end_date

        FROM subscriptions

        WHERE user_id=%s

        AND status='Active'

        AND end_date >= NOW()

        ORDER BY end_date DESC

        LIMIT 1

    """, (user_id,))


    if not subscription:

        return jsonify({

            "success": True,

            "subscribed": False,

            "subscription": None

        })


    # Convert database dates to strings

    if subscription.get("start_date"):

        subscription["start_date"] = \
            subscription["start_date"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )


    if subscription.get("end_date"):

        subscription["end_date"] = \
            subscription["end_date"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )


    return jsonify({

        "success": True,

        "subscribed": True,

        "subscription": subscription

    })