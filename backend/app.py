from flask import Flask, jsonify
from flask_cors import CORS
from routes.machines import machines
from routes.login import login
from routes.register import register
from routes.students import students
from routes.admin import admin
from routes.laundromats import laundromats
from routes.bookings import bookings
from routes.dashboard import dashboard
from routes.payments import payments
from routes.orders import orders
from routes.services import services
from routes.auth import auth
from routes.settings import settings
from routes.subscriptions import subscriptions
from routes.booking_payments import booking_payments
from routes.reviews import reviews
from routes.notifications import notifications
from routes.create_admin import create_admin
from flask import Flask, jsonify, send_from_directory
import os
app = Flask(__name__)
create_admin()
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500",
                "https://laundry-frontend-zu8i.onrender.com"
            ]
        }
    },
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# Register Blueprints
app.register_blueprint(booking_payments)
app.register_blueprint(subscriptions)
app.register_blueprint(auth)
app.register_blueprint(register)
app.register_blueprint(login)
app.register_blueprint(students)
app.register_blueprint(laundromats)
app.register_blueprint(bookings)
app.register_blueprint(payments)
app.register_blueprint(dashboard)
app.register_blueprint(orders)
app.register_blueprint(machines)
app.register_blueprint(services)
app.register_blueprint(admin)
app.register_blueprint(reviews)
app.register_blueprint(settings)
app.register_blueprint(notifications)
@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "Campus Laundry Connect API is running"
    })

@app.route("/uploads/laundromats/<filename>")
def laundromat_logo(filename):

    return send_from_directory(
        os.path.join(
            os.getcwd(),
            "uploads",
            "laundromats"
        ),
        filename
    )

@app.route("/uploads/students/<filename>")
def uploaded_student_profile_picture(filename):

    return send_from_directory(
        "uploads/students",
        filename
    )

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
