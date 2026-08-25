from flask import Blueprint, request, jsonify

from database import fetch_all, fetch_one, execute_query

services = Blueprint("services", __name__)
# ==========================================
# GET SERVICES FOR A LAUNDROMAT
# ==========================================

@services.route("/services/laundromat/<int:laundromat_id>", methods=["GET"])
def get_laundromat_services(laundromat_id):

    query = """
        SELECT
            services.id,
            services.laundromat_id,
            services.name,
            services.description,
            services.price,
            services.duration,
            services.status,
            laundromats.business_name

        FROM services

        INNER JOIN laundromats
            ON services.laundromat_id = laundromats.id

        WHERE services.laundromat_id = %s

        ORDER BY services.name
    """

    result = fetch_all(
        query,
        (laundromat_id,)
    )

    return jsonify({
        "success": True,
        "services": result
    })
# GET ONE SERVICE
# ==========================================

@services.route("/services/<int:id>", methods=["GET"])
def get_service(id):

    query = """

        SELECT

            services.*,

            laundromats.business_name

        FROM services

        INNER JOIN laundromats
            ON services.laundromat_id = laundromats.id

        WHERE services.id = %s

    """

    service = fetch_one(
        query,
        (id,)
    )

    if not service:

        return jsonify({

            "success": False,

            "message": "Service not found"

        }), 404


    return jsonify({

        "success": True,

        "service": service

    })


# ==========================================
# ADD SERVICE
# ==========================================

@services.route("/services", methods=["POST"])
def create_service():

    data = request.get_json()

    required = [
        "laundromat_id",
        "name",
        "price"
    ]

    for field in required:

        if not data.get(field):

            return jsonify({

                "success": False,

                "message":
                    f"{field} is required"

            }), 400


    query = """

        INSERT INTO services
        (
            laundromat_id,
            name,
            description,
            price,
            duration,
            status
        )

        VALUES
        (
            %s,%s,%s,%s,%s,%s
        )

    """

    success = execute_query(

        query,

        (
            data["laundromat_id"],
            data["name"],
            data.get("description", ""),
            data["price"],
            data.get("duration", ""),
            data.get("status", "Active")
        )

    )


    if success:

        return jsonify({

            "success": True,

            "message":
                "Service created successfully"

        }), 201


    return jsonify({

        "success": False,

        "message":
            "Unable to create service"

    }), 500


# ==========================================
# UPDATE SERVICE
# ==========================================

@services.route("/services/<int:id>", methods=["PUT"])
def update_service(id):

    data = request.get_json()

    query = """

        UPDATE services

        SET

            name=%s,
            description=%s,
            price=%s,
            duration=%s,
            status=%s

        WHERE id=%s

    """

    success = execute_query(

        query,

        (
            data.get("name"),
            data.get("description", ""),
            data.get("price"),
            data.get("duration", ""),
            data.get("status", "Active"),
            id
        )

    )


    if success:

        return jsonify({

            "success": True,

            "message":
                "Service updated successfully"

        })


    return jsonify({

        "success": False,

        "message":
            "Unable to update service"

    }), 500


# ==========================================
# DELETE SERVICE
# ==========================================

@services.route("/services/<int:id>", methods=["DELETE"])
def delete_service(id):

    success = execute_query(

        """
        DELETE FROM services
        WHERE id=%s
        """,

        (id,)

    )


    if success:

        return jsonify({

            "success": True,

            "message":
                "Service deleted successfully"

        })


    return jsonify({

        "success": False,

        "message":
            "Unable to delete service"

    }), 500

