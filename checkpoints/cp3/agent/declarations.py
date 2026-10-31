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

CHECK_AVAILABILITY = {
    "name": "check_availability",
    "description": (
        "Find meeting rooms that are free for a time slot and fit the group. "
        "Returns bookable offers (each with an offer_id and the real price) or nearby "
        "alternative slots. Only call when you know date, start time, end time and head count."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Date in YYYY-MM-DD (IST)."},
            "start_time": {"type": "string", "description": "Start, 24h HH:MM, e.g. 14:00"},
            "end_time": {"type": "string", "description": "End, 24h HH:MM, e.g. 16:00"},
            "capacity": {"type": "integer", "description": "Number of people attending."},
        },
        "required": ["date", "start_time", "end_time", "capacity"],
    },
}

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

TOOL_DECLARATIONS = [LOOKUP_CUSTOMER, CHECK_AVAILABILITY, CREATE_BOOKING]
