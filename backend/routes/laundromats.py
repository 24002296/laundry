from flask import Blueprint, request, jsonify
from database import fetch_all, fetch_one, execute_query

import os
import uuid


laundromats = Blueprint(
    "laundromats",
    __name__
)


# ============================================================
# UPLOAD SETTINGS
# ============================================================

UPLOAD_FOLDER = os.path.join(
    os.getcwd(),
    "uploads",
    "laundromats"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# GET ALL LAUNDROMATS
# ============================================================

@laundromats.route("/laundromats", methods=["GET"])
def get_laundromats():

    query = """
        SELECT
            laundromats.id,
            laundromats.user_id,
            laundromats.logo,

            users.first_name,
            users.last_name,
            users.email,
            users.phone,

            laundromats.business_name,
            laundromats.business_address,
            laundromats.rating,
            laundromats.bookings,
            laundromats.status

        FROM laundromats

        INNER JOIN users
            ON laundromats.user_id = users.id

        ORDER BY laundromats.business_name
    """

    result = fetch_all(query)

    return jsonify({
        "success": True,
        "laundromats": result or []
    })


# ============================================================
# GET LAUNDROMAT BY USER ID
# ============================================================

@laundromats.route(
    "/laundromats/user/<int:user_id>",
    methods=["GET"]
)
def get_laundromat_by_user(user_id):

    query = """
        SELECT

            laundromats.id,
            laundromats.user_id,
            laundromats.logo,

            users.first_name,
            users.last_name,
            users.email,
            users.phone,

            laundromats.business_name,
            laundromats.business_address,
            laundromats.rating,
            laundromats.bookings,
            laundromats.status

        FROM laundromats

        INNER JOIN users
            ON laundromats.user_id = users.id

        WHERE laundromats.user_id = %s

        LIMIT 1
    """

    shop = fetch_one(
        query,
        (user_id,)
    )

    if not shop:

        return jsonify({
            "success": False,
            "message": "Laundromat profile not found."
        }), 404

    return jsonify({
        "success": True,
        "laundromat": shop
    })


# ============================================================
# GET ONE LAUNDROMAT
# ============================================================

@laundromats.route(
    "/laundromats/<int:id>",
    methods=["GET"]
)
def get_laundromat(id):

    query = """

        SELECT

            laundromats.id,
            laundromats.user_id,

            users.first_name,
            users.last_name,
            users.email,
            users.phone,

            laundromats.business_name,
            laundromats.business_address,
            laundromats.rating,
            laundromats.bookings,
            laundromats.status,
            laundromats.logo

        FROM laundromats

        INNER JOIN users
            ON laundromats.user_id = users.id

        WHERE laundromats.id = %s

    """

    shop = fetch_one(
        query,
        (id,)
    )

    if not shop:

        return jsonify({
            "success": False,
            "message": "Laundromat not found."
        }), 404

    return jsonify({
        "success": True,
        "laundromat": shop
    })


# ============================================================
# APPROVE LAUNDROMAT
# ============================================================

@laundromats.route(
    "/laundromats/<int:id>/approve",
    methods=["PUT"]
)
def approve_laundromat(id):

    success = execute_query(
        """
        UPDATE laundromats
        SET status = 'Approved'
        WHERE id = %s
        """,
        (id,)
    )

    if not success:

        return jsonify({
            "success": False,
            "message": "Unable to approve laundromat."
        }), 500

    return jsonify({
        "success": True,
        "message": "Laundromat approved."
    })


# ============================================================
# SUSPEND LAUNDROMAT
# ============================================================

@laundromats.route(
    "/laundromats/<int:id>/suspend",
    methods=["PUT"]
)
def suspend_laundromat(id):

    success = execute_query(
        """
        UPDATE laundromats
        SET status = 'Suspended'
        WHERE id = %s
        """,
        (id,)
    )

    if not success:

        return jsonify({
            "success": False,
            "message": "Unable to suspend laundromat."
        }), 500

    return jsonify({
        "success": True,
        "message": "Laundromat suspended."
    })


# ============================================================
# UPDATE LAUNDROMAT
# ============================================================

@laundromats.route(
    "/laundromats/<int:id>",
    methods=["PUT"]
)
def update_laundromat(id):

    data = request.get_json() or {}

    business_name = data.get("business_name")
    business_address = data.get("business_address")
    phone = data.get("phone")

    if not business_name:

        return jsonify({
            "success": False,
            "message": "Business name is required."
        }), 400

    success = execute_query(
        """
        UPDATE laundromats
        SET
            business_name = %s,
            business_address = %s
        WHERE id = %s
        """,
        (
            business_name,
            business_address,
            id
        )
    )

    if phone is not None:

        shop = fetch_one(
            """
            SELECT user_id
            FROM laundromats
            WHERE id = %s
            """,
            (id,)
        )

        if shop:

            execute_query(
                """
                UPDATE users
                SET phone = %s
                WHERE id = %s
                """,
                (
                    phone,
                    shop["user_id"]
                )
            )

    if not success:

        return jsonify({
            "success": False,
            "message": "Unable to update laundromat."
        }), 500

    return jsonify({
        "success": True,
        "message": "Laundromat updated successfully."
    })


# ============================================================
# DELETE LAUNDROMAT
# ============================================================

@laundromats.route(
    "/laundromats/<int:id>",
    methods=["DELETE"]
)
def delete_laundromat(id):

    shop = fetch_one(
        """
        SELECT user_id
        FROM laundromats
        WHERE id = %s
        """,
        (id,)
    )

    if not shop:

        return jsonify({
            "success": False,
            "message": "Laundromat not found."
        }), 404

    execute_query(
        """
        DELETE FROM users
        WHERE id = %s
        """,
        (shop["user_id"],)
    )

    return jsonify({
        "success": True,
        "message": "Laundromat deleted."
    })


# ============================================================
# SEARCH LAUNDROMATS
# ============================================================

@laundromats.route(
    "/laundromats/search/<string:keyword>",
    methods=["GET"]
)
def search_laundromats(keyword):

    search = "%" + keyword + "%"

    query = """

        SELECT

            laundromats.id,
            users.first_name,
            users.last_name,
            laundromats.business_name,
            laundromats.business_address,
            laundromats.status

        FROM laundromats

        INNER JOIN users
            ON laundromats.user_id = users.id

        WHERE

            laundromats.business_name LIKE %s

            OR users.first_name LIKE %s

            OR users.last_name LIKE %s

    """

    result = fetch_all(
        query,
        (
            search,
            search,
            search
        )
    )

    return jsonify({
        "success": True,
        "laundromats": result or []
    })


# ============================================================
# UPLOAD LAUNDROMAT LOGO
# ============================================================

@laundromats.route(
    "/laundromats/<int:id>/logo",
    methods=["POST"]
)
def upload_laundromat_logo(id):

    if "logo" not in request.files:

        return jsonify({
            "success": False,
            "message": "No logo file selected."
        }), 400

    file = request.files["logo"]

    if file.filename == "":

        return jsonify({
            "success": False,
            "message": "No logo file selected."
        }), 400

    if not allowed_file(file.filename):

        return jsonify({
            "success": False,
            "message":
                "Only PNG, JPG, JPEG and WEBP images are allowed."
        }), 400

    laundromat = fetch_one(
        """
        SELECT id, logo
        FROM laundromats
        WHERE id = %s
        """,
        (id,)
    )

    if not laundromat:

        return jsonify({
            "success": False,
            "message": "Laundromat not found."
        }), 404

    extension = (
        file.filename
        .rsplit(".", 1)[1]
        .lower()
    )

    filename = (
        str(uuid.uuid4())
        + "."
        + extension
    )

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(filepath)

    old_picture = laundromat.get("logo")

    if old_picture:

        old_path = os.path.join(
            UPLOAD_FOLDER,
            old_picture
        )

        if os.path.exists(old_path):

            try:
                os.remove(old_path)

            except Exception as error:

                print(
                    "Unable to delete old logo:",
                    error
                )

    execute_query(
        """
        UPDATE laundromats
        SET logo = %s
        WHERE id = %s
        """,
        (
            filename,
            id
        )
    )

    return jsonify({
        "success": True,
        "message": "Laundromat logo uploaded successfully.",
        "logo": filename
    })