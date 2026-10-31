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
    try:
        r = http.get(f"/bookings/{booking_id}")
    except httpx.HTTPError as e:
        return Verification(False, None, [f"could not read booking back: {type(e).__name__}"])
    if r.status_code == 404:
        return Verification(False, None, ["booking does not exist in the CRM"])
    if r.status_code != 200:
        return Verification(False, None, [f"read-back failed with HTTP {r.status_code}"])

    record = r.json()
    problems = [
        f"{f}: expected {expected[f]!r}, CRM has {record.get(f)!r}"
        for f in FIELDS
        if record.get(f) != expected[f]
    ]
    if record.get("status") != "confirmed":
        problems.append(f"status is {record.get('status')!r}, not 'confirmed'")
    return Verification(not problems, record, problems)
