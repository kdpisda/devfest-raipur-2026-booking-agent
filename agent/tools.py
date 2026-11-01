"""The read tools (prepared for you: read them, no need to edit).

Gemini *asks* for tools to be called. Python *decides* whether and how.
Every function returns a small JSON-able dict that is sent back to the model.
The one write, create_booking, lives in booking.py: that is today's work.
"""
from __future__ import annotations

import httpx

from .session import Session


def _detail(r: httpx.Response) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except Exception:
        return r.text


# --------------------------------------------------------------------------
# read-only tools (prepared)
# --------------------------------------------------------------------------
def lookup_customer(s: Session) -> dict:
    """Who is messaging us? Uses the trusted sender phone, never a model-chosen ID."""
    with s.http() as h:
        r = h.get("/customers/lookup", params={"phone": s.sender_phone})
    if r.status_code == 404:
        s.customer = None
        return {"status": "not_found", "reason": "this phone number is not in our CRM"}
    r.raise_for_status()
    s.customer = r.json()
    return {"status": "found", "name": s.customer["name"], "plan": s.customer["plan"],
            "company": s.customer["company"]}


def check_availability(s: Session, date: str, start_time: str, end_time: str,
                       capacity: int) -> dict:
    """Ask the CRM which rooms are free. Prices come from the CRM, never from the model."""
    if s.customer is None:
        return {"status": "error", "reason": "call lookup_customer first"}
    params = {"customer_id": s.customer["id"], "date": date, "start_time": start_time,
              "end_time": end_time, "capacity": int(capacity)}
    with s.http() as h:
        r = h.get("/rooms/availability", params=params)
    if r.status_code == 422:
        return {"status": "invalid_request", "reason": _detail(r)}
    r.raise_for_status()
    data = r.json()
    for opt in data["options"]:
        s.offers[opt["offer_id"]] = opt          # remember exactly what we showed
    return {
        "status": "ok",
        "options": [{k: v for k, v in o.items() if k != "room_id"} for o in data["options"]],
        "alternatives": data.get("alternatives", []),
        "unavailable_rooms": data.get("unavailable_rooms", []),
    }


# --------------------------------------------------------------------------
from .booking import create_booking  # noqa: E402  (the write: agent/booking.py)

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
    except (TypeError, KeyError) as e:
        return {"status": "error", "reason": f"crashed: {type(e).__name__}: {e}"}
    except httpx.HTTPError as e:
        return {"status": "error", "reason": f"CRM error: {type(e).__name__}"}
