from flask import Blueprint, jsonify, request
from database import fetch_all, fetch_one, execute_query

import os
import uuid
from werkzeug.utils import secure_filename


students = Blueprint("students", __name__)


# =====================================================
# UPLOAD SETTINGS
# =====================================================

UPLOAD_FOLDER = os.path.join(
    os.getcwd(),
    "uploads",
    "students"
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

# =====================================================
# GET ALL STUDENTS
# =====================================================

@students.route("/students", methods=["GET"])
def get_students():

    try:

        query = """
            SELECT
                users.id AS user_id,
                users.first_name,
                users.last_name,
                users.email,
                users.phone,

                students.id AS student_id,
                students.student_number,
                students.status,
                students.profile_picture

            FROM students

            INNER JOIN users
                ON students.user_id = users.id

            WHERE users.role = 'student'

            ORDER BY users.first_name ASC
        """

        students_list = fetch_all(query)

        return jsonify({
            "success": True,
            "students": students_list or []
        }), 200

    except Exception as error:

        print("GET STUDENTS ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to load students.",
            "students": []
        }), 500
# =====================================================
# GET ALL STUDENTS
# =====================================================
@students.route("/students-debug", methods=["GET"])
def students_debug():

    database = fetch_one("""
        SELECT
            DATABASE() AS database_name,
            @@hostname AS hostname,
            @@port AS port
    """)

    users = fetch_all("""
        SELECT
            id,
            first_name,
            last_name,
            email
        FROM users
        ORDER BY id
    """)

    students_data = fetch_all("""
        SELECT
            id,
            user_id,
            student_number,
            status,
            profile_picture
        FROM students
        ORDER BY id
    """)

    return jsonify({

        "database_info": database,

        "users": users,

        "students": students_data

    })

# =====================================================
# GET ONE STUDENT
# =====================================================
@students.route("/students/<int:user_id>", methods=["GET"])
def get_student(user_id):

    print("\n==============================")
    print("GET STUDENT")
    print("Received user_id:", user_id)

    # TEST 1: Find student directly
    student = fetch_one(
        """
        SELECT *
        FROM students
        WHERE user_id = %s
        """,
        (user_id,)
    )

    print("Student table result:", student)

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found.",
            "debug_user_id": user_id
        }), 404

    # TEST 2: Get user information
    user = fetch_one(
        """
        SELECT
            id,
            first_name,
            last_name,
            email,
            phone
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    print("User table result:", user)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found.",
            "debug_user_id": user_id
        }), 404

    return jsonify({
        "success": True,
        "student": {
            "user_id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
            "phone": user["phone"],

            "student_id": student["id"],
            "student_number": student["student_number"],
            "status": student["status"],
            "profile_picture": student.get("profile_picture")
        }
    })
# =====================================================
# UPDATE STUDENT
# =====================================================

@students.route("/students/<int:id>", methods=["PUT"])
def update_student(id):

    data = request.get_json(silent=True) or {}

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    phone = data.get("phone")
    status = data.get("status")

    if not first_name:
        return jsonify({
            "success": False,
            "message": "First name is required."
        }), 400

    if not last_name:
        return jsonify({
            "success": False,
            "message": "Last name is required."
        }), 400

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    # Update user information
    success = execute_query(
        """
        UPDATE users
        SET
            first_name = %s,
            last_name = %s,
            email = %s,
            phone = %s
        WHERE id = %s
        """,
        (
            first_name,
            last_name,
            email,
            phone,
            id
        )
    )

    if not success:
        return jsonify({
            "success": False,
            "message": "Unable to update student information."
        }), 500

    # Update student status
    if status:

        execute_query(
            """
            UPDATE students
            SET status = %s
            WHERE user_id = %s
            """,
            (
                status,
                id
            )
        )

    return jsonify({
        "success": True,
        "message": "Student updated successfully."
    }), 200
# =====================================================
# DELETE STUDENT
# =====================================================

@students.route("/students/<int:id>", methods=["DELETE"])
def delete_student(id):

    try:

        student = fetch_one(
            """
            SELECT user_id
            FROM students
            WHERE user_id = %s
            """,
            (id,)
        )

        if not student:

            return jsonify({
                "success": False,
                "message": "Student not found."
            }), 404

        # Delete student record first
        execute_query(
            """
            DELETE FROM students
            WHERE user_id = %s
            """,
            (id,)
        )

        # Then delete user
        execute_query(
            """
            DELETE FROM users
            WHERE id = %s
            AND role = 'student'
            """,
            (id,)
        )

        return jsonify({
            "success": True,
            "message": "Student deleted successfully."
        }), 200

    except Exception as error:

        print("DELETE STUDENT ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to delete student."
        }), 500
# =====================================================
# UPLOAD STUDENT PROFILE PICTURE
# =====================================================

@students.route(
    "/students/<int:id>/profile-picture",
    methods=["POST"]
)
def upload_student_profile_picture(id):

    # -----------------------------------------------
    # Check file
    # -----------------------------------------------

    if "profile_picture" not in request.files:

        return jsonify({

            "success": False,
            "message":
                "No profile picture selected."

        }), 400


    file = request.files["profile_picture"]


    if file.filename == "":

        return jsonify({

            "success": False,
            "message":
                "No profile picture selected."

        }), 400


    # -----------------------------------------------
    # Check extension
    # -----------------------------------------------

    if not allowed_file(file.filename):

        return jsonify({

            "success": False,
            "message":
                "Only PNG, JPG, JPEG and WEBP images are allowed."

        }), 400


    # -----------------------------------------------
    # Find student
    # -----------------------------------------------

    student = fetch_one(

        """
        SELECT
            user_id,
            profile_picture

        FROM students

        WHERE user_id = %s

        LIMIT 1
        """,

        (id,)

    )


    if not student:

        return jsonify({

            "success": False,
            "message": "Student not found."

        }), 404


    # -----------------------------------------------
    # Generate filename
    # -----------------------------------------------

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


    # -----------------------------------------------
    # Save file
    # -----------------------------------------------

    file.save(filepath)


    # -----------------------------------------------
    # Delete old picture
    # -----------------------------------------------

    old_picture = student.get(
        "profile_picture"
    )


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
                    "Unable to delete old picture:",
                    error
                )


    # -----------------------------------------------
    # Save filename in database
    # -----------------------------------------------

    execute_query(

        """
        UPDATE students

        SET profile_picture = %s

        WHERE user_id = %s
        """,

        (
            filename,
            id
        )

    )


    return jsonify({

        "success": True,

        "message":
            "Profile picture uploaded successfully.",

        "profile_picture":
            filename

    })

@students.route("/debug-student-2", methods=["GET"])
def debug_student_2():

    result = fetch_one("""
        SELECT *
        FROM students
        WHERE user_id = 2
    """)

    return jsonify({
        "success": True,
        "student": result
    })