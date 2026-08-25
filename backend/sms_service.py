import os

from dotenv import load_dotenv
from twilio.rest import Client


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()


# ============================================================
# TWILIO CONFIGURATION
# ============================================================

TWILIO_ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_PHONE_NUMBER = os.getenv(
    "TWILIO_PHONE_NUMBER"
)

# ============================================================
# SEND SMS
# ============================================================

def send_sms(phone_number, message):

    try:

        if not phone_number:

            print(
                "SMS NOT SENT: No phone number."
            )

            return False


        if not TWILIO_ACCOUNT_SID:
            print(
                "SMS NOT SENT: "
                "TWILIO_ACCOUNT_SID is not configured."
            )

            return False


        if not TWILIO_AUTH_TOKEN:
            print(
                "SMS NOT SENT: "
                "TWILIO_AUTH_TOKEN is not configured."
            )

            return False


        if not TWILIO_PHONE_NUMBER:
            print(
                "SMS NOT SENT: "
                "TWILIO_PHONE_NUMBER is not configured."
            )

            return False


        # ----------------------------------------------------
        # Make sure South African numbers are E.164
        # ----------------------------------------------------

        phone_number = format_phone_number(
            phone_number
        )


        client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )


        sms = client.messages.create(

            body=message,

            from_=TWILIO_PHONE_NUMBER,

            to=phone_number

        )


        print(
            "SMS SENT:",
            sms.sid,
            "TO:",
            phone_number
        )


        return True


    except Exception as error:

        print(
            "SMS ERROR:",
            error
        )

        return False


# ============================================================
# FORMAT SOUTH AFRICAN PHONE NUMBER
# ============================================================

def format_phone_number(phone):

    if not phone:

        return None


    phone = str(phone).strip()


    # Remove spaces
    phone = phone.replace(
        " ",
        ""
    )


    # Already international
    if phone.startswith("+"):

        return phone


    # South African format:
    # 0821234567
    #
    # becomes:
    # +27821234567

    if phone.startswith("0"):

        return "+27" + phone[1:]


    # Handle 27XXXXXXXXX

    if phone.startswith("27"):

        return "+" + phone


    return phone

print("TWILIO SID LOADED:", bool(TWILIO_ACCOUNT_SID))
print("TWILIO TOKEN LOADED:", bool(TWILIO_AUTH_TOKEN))
print("TWILIO PHONE LOADED:", bool(TWILIO_PHONE_NUMBER))