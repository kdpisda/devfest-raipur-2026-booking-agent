"""Outcome verification: did the thing ACTUALLY happen?

A fluent "Booked!" is not proof. A 201 response is not proof either.
A booking ID is just a pointer: we read the stored record back and compare.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx

FIELDS = ("customer_id", "room_id", "date", "start_time", "end_time")


@dataclass
class Verification:
    ok: bool
    record: dict | None = None
    problems: list[str] = field(default_factory=list)


def verify_booking(http: httpx.Client, booking_id: str, expected: dict) -> Verification:
    """Read the booking back from the CRM and compare it with what the customer approved.

    expected = {"customer_id", "room_id", "date", "start_time", "end_time"}
    """
    # TODO 5 ─ trust, but verify                                        (Step 3)
    #
    #   1. r = http.get(f"/bookings/{booking_id}")
    #        httpx.HTTPError → Verification(False, None, ["could not read booking back: ..."])
    #        404             → Verification(False, None, ["booking does not exist in the CRM"])
    #        not 200         → Verification(False, None, [f"read-back failed with HTTP ..."])
    #   2. record = r.json()
    #   3. For each f in FIELDS: if record[f] != expected[f], add a problem like
    #        f"{f}: expected {expected[f]!r}, CRM has {record.get(f)!r}"
    #   4. If record["status"] != "confirmed": add f"status is {...!r}, not 'confirmed'"
    #   5. return Verification(ok=not problems, record=record, problems=problems)
    #
    # Until you do this, every booking comes back "not_verified" and the agent
    # (correctly!) refuses to claim success.
    return Verification(False, None, ["verification not implemented yet (TODO 5)"])
