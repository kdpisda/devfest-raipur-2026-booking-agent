"""The tools: plain Python functions that talk to the CRM over HTTP.

Gemini *asks* for these to be called. Python *decides* whether and how.
Every function returns a small JSON-able dict that is sent back to the model.
"""
from __future__ import annotations

import httpx

from .session import Session
from .verify import verify_booking


def _detail(r: httpx.Response) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except Exception:
        return r.text


# --------------------------------------------------------------------------
# CHECKPOINT 1 · read-only tools
# --------------------------------------------------------------------------
def lookup_customer(s: Session) -> dict:
    """Who is messaging us? Uses the trusted sender phone, never a model-chosen ID."""
    # TODO 2 ─ look the sender up in the CRM                         (Checkpoint 1)
    #
    #   GET /customers/lookup?phone=<s.sender_phone>
    #     404 → s.customer = None
    #           return {"status": "not_found", "reason": "..."}
    #     200 → s.customer = r.json()            # keep the FULL record on the session
    #           return {"status": "found", "name": ..., "plan": ..., "company": ...}
    #
    #   Hint:  with s.http() as h:
    #              r = h.get("/customers/lookup", params={"phone": s.sender_phone})
    #
    #   Why the phone and not an argument? Because a model-chosen customer ID is
    #   how you end up booking on someone else's account.
    raise NotImplementedError("TODO 2: lookup_customer")


def check_availability(s: Session, date: str, start_time: str, end_time: str,
                       capacity: int) -> dict:
    """Ask the CRM which rooms are free. Prices come from the CRM, never from the model."""
    # TODO 3 ─ check availability                                      (Checkpoint 1)
    #
    #   1. If s.customer is None → return {"status": "error", "reason": "call lookup_customer first"}
    #   2. GET /rooms/availability with params:
    #        customer_id=s.customer["id"], date, start_time, end_time, capacity=int(capacity)
    #   3. 422 → return {"status": "invalid_request", "reason": _detail(r)}
    #        (bad input is DATA the model can fix, not a crash)
    #   4. For every option in data["options"]: s.offers[opt["offer_id"]] = opt
    #        (later, only offers we actually showed can be booked)
    #   5. return {"status": "ok",
    #              "options": options WITHOUT the internal "room_id" key,
    #              "alternatives": data["alternatives"],
    #              "unavailable_rooms": data["unavailable_rooms"]}
    raise NotImplementedError("TODO 3: check_availability")


# --------------------------------------------------------------------------
# CHECKPOINT 2 · the write: confirmation gate + create
# --------------------------------------------------------------------------
NOT_DONE = ("Do NOT tell the customer it is booked. Do not retry on your own. "
            "Tell them honestly what happened and that a team member will follow up.")


def create_booking(s: Session, offer_id: str) -> dict:
    # TODO 4 ─ the write                                                (Checkpoint 2)
    #
    #   1. offer = s.offers.get(offer_id)
    #        None → return {"status": "rejected", "reason": "unknown offer_id ..."}
    #        (the model can hallucinate IDs; we only book what we showed)
    #   2. s.customer is None → {"status": "rejected", ...}
    #   3. THE GATE:  if not s.naive and not s.confirm(offer):
    #                     return {"status": "not_confirmed", "reason": "..."}
    #   4. key = f"{s.customer['id']}:{offer_id}"          # idempotency key
    #      expected = {customer_id, room_id, date, start_time, end_time}  (from s.customer + offer)
    #   5. with s.http() as h:
    #          POST /bookings  json={"customer_id": ..., "offer_id": offer_id}
    #                          headers={"Idempotency-Key": key}
    #        httpx.TimeoutException → return _reconcile(s, h, key, expected)   (bonus, prepared)
    #        other httpx.HTTPError  → {"status": "failed", ..., "instruction": NOT_DONE}
    #        409 → {"status": "conflict", ...}     410 → {"status": "expired", ...}
    #        other >= 400 → {"status": "failed", ..., "instruction": NOT_DONE}
    #   6. booking = r.json()
    #        if s.naive: return {"status": "booked", "booking_id": booking["id"]}
    #        return _verified_result(s, h, booking["id"], expected, offer)
    raise NotImplementedError("TODO 4: create_booking")


# --------------------------------------------------------------------------
# CHECKPOINT 3 · verification (see verify.py) wired into the result
# --------------------------------------------------------------------------
def _verified_result(s: Session, h: httpx.Client, booking_id: str, expected: dict,
                     offer: dict) -> dict:
    v = verify_booking(h, booking_id, expected)
    if v.ok:
        s.verified[booking_id] = {**v.record, "room": offer["room"]}
        return {"status": "verified", "booking_id": booking_id, "room": offer["room"],
                "date": offer["date"], "start_time": offer["start_time"],
                "end_time": offer["end_time"], "price_inr": v.record["price_inr"]}
    s.log(f"VERIFICATION FAILED for {booking_id}: {v.problems}")
    return {"status": "not_verified", "booking_id": booking_id, "problems": v.problems,
            "instruction": NOT_DONE}


def _reconcile(s: Session, h: httpx.Client, key: str, expected: dict) -> dict:
    """BONUS (advanced): after a timeout, find the booking by idempotency key."""
    try:
        found = h.get("/bookings", params={"idempotency_key": key}).json()
    except httpx.HTTPError:
        found = []
    if len(found) == 1:
        offer = next(o for o in s.offers.values() if o["room_id"] == expected["room_id"]
                     and o["date"] == expected["date"] and o["start_time"] == expected["start_time"])
        return _verified_result(s, h, found[0]["id"], expected, offer)
    return {"status": "unknown", "reason": "CRM timed out and no booking could be found",
            "instruction": NOT_DONE}


# --------------------------------------------------------------------------
TOOLS = {
    "lookup_customer": lookup_customer,
    "check_availability": check_availability,
    "create_booking": create_booking,
}


def dispatch(s: Session, name: str, args: dict) -> dict:
    """Run the tool Gemini asked for. Errors become data the model can read, not crashes."""
    fn = TOOLS.get(name)
    if fn is None:
        return {"status": "error", "reason": f"unknown tool {name!r}"}
    try:
        return fn(s, **args)
    except NotImplementedError as e:
        return {"status": "error", "reason": f"tool not implemented yet ({e})"}
    except TypeError as e:
        return {"status": "error", "reason": f"bad arguments: {e}"}
    except httpx.HTTPError as e:
        return {"status": "error", "reason": f"CRM error: {type(e).__name__}"}
