"""Tool declarations: the *menu* we show Gemini.

The model reads these names + descriptions to decide WHEN to call a tool and
WHAT arguments to send. Good descriptions are half the battle.

Notice what is missing: no customer_id, no price, no room_id on create_booking.
The model can't book for someone else or invent a price, because it can't
even express that.
"""

LOOKUP_CUSTOMER = {
    "name": "lookup_customer",
    "description": (
        "Look up the customer who sent this message in the CRM. The application already "
        "knows their phone number, so this takes no arguments. Call this first."
    ),
    "parameters": {"type": "object", "properties": {}},
}

# TODO 1 ─ declare check_availability                                (Checkpoint 1)
#
#   Copy the shape of LOOKUP_CUSTOMER / CREATE_BOOKING. You need:
#     name: "check_availability"
#     description: when to use it (be specific: "only when you know date, time and head count")
#     parameters: date (YYYY-MM-DD), start_time (24h HH:MM), end_time (24h HH:MM),
#                 capacity (integer = number of people) — all four required.
#
#   Tip: describe the FORMAT in each description. That's how "kal 2 baje" becomes "14:00".
CHECK_AVAILABILITY = None

CREATE_BOOKING = {
    "name": "create_booking",
    "description": (
        "Book one offer returned by check_availability. Only call AFTER the customer has "
        "clearly agreed to that specific room, date and time. The application will ask the "
        "customer to tap Confirm, create the booking, and verify it. Never tell the customer "
        "a booking is done unless this returns status 'verified'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "offer_id": {"type": "string", "description": "offer_id from check_availability"},
        },
        "required": ["offer_id"],
    },
}

TOOL_DECLARATIONS = [d for d in (LOOKUP_CUSTOMER, CHECK_AVAILABILITY, CREATE_BOOKING) if d]
