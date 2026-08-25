from flask import Blueprint, jsonify, request

from database import fetch_all, fetch_one, execute_query


machines = Blueprint("machines", __name__)


# ==========================================
# GET MACHINES FOR LAUNDROMAT USER
# ==========================================

@machines.route("/machines/laundromat/<int:user_id>", methods=["GET"])
def get_laundromat_machines(user_id):

    query = """

        SELECT

            machines.id,
            machines.name,
            machines.type,
            machines.status,
            machines.created_at,

            laundromats.id AS laundromat_id,
            laundromats.business_name

        FROM machines

        INNER JOIN laundromats

            ON machines.laundromat_id =
               laundromats.id

        WHERE laundromats.user_id = %s

        ORDER BY machines.id ASC

    """

    result = fetch_all(
        query,
        (user_id,)
    )


    return jsonify({

        "success": True,

        "machines": result

    })


# ==========================================
# GET SINGLE MACHINE
# ==========================================

@machines.route("/machines/<int:id>", methods=["GET"])
def get_machine(id):

    query = """

        SELECT

            machines.id,
            machines.name,
            machines.type,
            machines.status,
            machines.laundromat_id

        FROM machines

        WHERE machines.id = %s

    """

    machine = fetch_one(
        query,
        (id,)
    )


    if not machine:

        return jsonify({

            "success": False,

            "message": "Machine not found"

        }), 404


    return jsonify({

        "success": True,

        "machine": machine

    })


# ==========================================
# ADD MACHINE
# ==========================================

@machines.route("/machines", methods=["POST"])
def add_machine():

    data = request.get_json(silent=True)

    print("MACHINE DATA RECEIVED:", data)

    if not data:

        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    user_id = data.get("laundromat_id")
    name = data.get("name")
    machine_type = data.get("type")
    status = data.get("status", "Available")

    if not user_id or not name or not machine_type:

        return jsonify({
            "success": False,
            "message": "User, name and type are required"
        }), 400

    # Find the actual laundromat ID belonging to this user
    laundromat = fetch_one(
        """
        SELECT id
        FROM laundromats
        WHERE user_id=%s
        """,
        (user_id,)
    )

    if not laundromat:

        return jsonify({
            "success": False,
            "message": "Laundromat account not found"
        }), 404

    laundromat_id = laundromat["id"]

    print("USER ID:", user_id)
    print("LAUNDROMAT ID:", laundromat_id)

    query = """
        INSERT INTO machines
        (
            laundromat_id,
            name,
            type,
            status
        )
        VALUES (%s, %s, %s, %s)
    """

    success = execute_query(
        query,
        (
            laundromat_id,
            name,
            machine_type,
            status
        )
    )

    if success:

        return jsonify({
            "success": True,
            "message": "Machine added successfully"
        }), 201

    return jsonify({
        "success": False,
        "message": "Unable to add machine"
    }), 500
# ==========================================
# UPDATE MACHINE STATUS
# ==========================================

@machines.route("/machines/<int:id>", methods=["PUT"])
def update_machine(id):

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    status = data.get("status")

    if not status:

        return jsonify({
            "success": False,
            "message": "Status is required"
        }), 400

    query = """
        UPDATE machines
        SET status=%s
        WHERE id=%s
    """

    success = execute_query(
        query,
        (status, id)
    )

    if success:

        return jsonify({
            "success": True,
            "message": "Machine status updated successfully"
        })

    return jsonify({
        "success": False,
        "message": "Unable to update machine"
    }), 500


# ==========================================
# DELETE MACHINE
# ==========================================

@machines.route("/machines/<int:id>", methods=["DELETE"])
def delete_machine(id):

    machine = fetch_one(
        "SELECT id FROM machines WHERE id=%s",
        (id,)
    )

    if not machine:

        return jsonify({
            "success": False,
            "message": "Machine not found"
        }), 404

    success = execute_query(
        "DELETE FROM machines WHERE id=%s",
        (id,)
    )

    if success:

        return jsonify({
            "success": True,
            "message": "Machine deleted successfully"
        })

    return jsonify({
        "success": False,
        "message": "Unable to delete machine"
    }), 500