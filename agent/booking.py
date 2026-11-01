"""agent/booking.py — THE ONLY FILE YOU EDIT TODAY.

Pisda ji's beta wrote this over a Sunday night. It "works": Gemini says
"Done! Booked." Then Priya walks in at 2 PM and there is no booking.

Everything else (Gemini loop, reads, CRM) is already built and correct.
The bug lives in the three functions below. One step = one function.

    create_booking()                  ← Gemini calls this (already wired up)
      ├─ STEP 1  check_approval()     did the customer really say yes?
      ├─ STEP 2  write_booking()      write it once, and be honest when it fails
      └─ STEP 3  prove_it()           read it back before we say "booked"
"""
from __future__ import annotations

import httpx

from .session import Session

NOT_DONE = ("Do NOT tell the customer it is booked. Do not retry on your own. "
            "Tell them honestly what happened and that a team member will follow up.")


# ───────────────────────────── prepared helpers (read, don't edit) ──────────
def failed(reason: str) -> dict:
    return {"status": "failed", "reason": reason, "instruction": NOT_DONE}


def not_verified(booking_id: str, problems: list[str]) -> dict:
    return {"status": "not_verified", "booking_id": booking_id, "problems": problems,
            "instruction": NOT_DONE}


def receipt(s: Session, record: dict, offer: dict) -> dict:
    """The only way to say "verified": remember the record and return the facts."""
    s.verified[record["id"]] = {**record, "room": offer["room"]}
    return {"status": "verified", "booking_id": record["id"], "room": offer["room"],
            "date": record["date"], "start_time": record["start_time"],
            "end_time": record["end_time"], "price_inr": record["price_inr"]}


def find_by_key(s: Session, key: str) -> tuple[dict | None, dict | None]:
    """After a timeout the write MAY have happened. Look it up instead of guessing."""
    with s.http() as h:
        try:
            found = h.get("/bookings", params={"idempotency_key": key}).json()
        except httpx.HTTPError:
            found = []
    if len(found) == 1:
        return found[0], None
    return None, {"status": "unknown", "reason": "CRM timed out and no booking was found",
                  "instruction": NOT_DONE}


# ───────────────────────────── the whole flow (read, don't edit) ────────────
def create_booking(s: Session, offer_id: str) -> dict:
    if s.customer is None:
        return {"status": "rejected", "reason": "call lookup_customer first"}

    if s.naive:                                   # the villain, kept for the demo
        offer = s.offers[offer_id]
        booking, _ = write_booking_naive(s, offer)
        return {"status": "booked", "booking_id": booking["id"]}

    offer, problem = check_approval(s, offer_id)          # STEP 1
    if problem:
        return problem

    booking, problem = write_booking(s, offer)            # STEP 2
    if problem:
        return problem

    return prove_it(s, booking["id"], offer)              # STEP 3


def write_booking_naive(s: Session, offer: dict):
    with s.http() as h:
        r = h.post("/bookings", json={"customer_id": s.customer["id"], "offer_id": offer["offer_id"]})
    return r.json(), None


# ═════════════════════════════ STEP 1 ════════════════════════════════════════
def check_approval(s: Session, offer_id: str) -> tuple[dict | None, dict | None]:
    # 🐞 Pisda ji's beta: "Gemini said they agreed. Good enough."
    #
    # TODO STEP 1 · did the customer REALLY say yes?
    #   • unknown offer_id (the model made it up)  → None, {"status": "rejected", ...}
    #   • customer didn't tap Confirm: s.confirm(offer) is False
    #                                               → None, {"status": "not_confirmed", ...}
    #   • otherwise                                 → offer, None
    return s.offers.get(offer_id), None


# ═════════════════════════════ STEP 2 ════════════════════════════════════════
def write_booking(s: Session, offer: dict) -> tuple[dict | None, dict | None]:
    # 🐞 Pisda ji's beta: fire and forget.
    #
    # TODO STEP 2 · write it ONCE, and be honest when it fails
    #   • key = f"{s.customer['id']}:{offer['offer_id']}"  → send as header "Idempotency-Key"
    #   • httpx.TimeoutException  → return find_by_key(s, key)      (prepared helper)
    #   • other httpx.HTTPError   → None, failed("could not reach the CRM")
    #   • 409                     → None, {"status": "conflict", ...}
    #   • any other >= 400        → None, failed(f"CRM said HTTP {r.status_code}")
    #   • otherwise               → r.json(), None
    with s.http() as h:
        r = h.post("/bookings",
                   json={"customer_id": s.customer["id"], "offer_id": offer["offer_id"]})
    return r.json(), None


# ═════════════════════════════ STEP 3 ════════════════════════════════════════
def prove_it(s: Session, booking_id: str, offer: dict) -> dict:
    # 🐞 Pisda ji's beta: "The API said 201. Ship it."
    #
    # TODO STEP 3 · read it back before you say "booked"
    #   • GET /bookings/{booking_id}
    #       404 or network error  → not_verified(booking_id, ["..."])   (prepared helper)
    #   • compare customer_id, room_id, date, start_time, end_time with what was approved
    #   • status must be "confirmed"
    #   • any problem → not_verified(booking_id, problems)
    #   • all good    → receipt(s, record, offer)                       (prepared helper)
    return receipt(s, {"id": booking_id, **offer}, offer)
