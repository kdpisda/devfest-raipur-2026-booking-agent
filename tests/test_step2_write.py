"""STEP 2 · write_booking · pytest tests/test_step2_write.py"""
from conftest import chaos, stored_bookings
from helpers import offer

from agent.booking import create_booking


def test_slot_taken_is_a_conflict_not_a_crash(crm, tomorrow):
    s1, oid1 = offer(crm, tomorrow)
    s2, oid2 = offer(crm, tomorrow, phone="+919800000002")
    create_booking(s2, oid2)                       # Arjun grabs Sirpur first
    r = create_booking(s1, oid1)
    assert r["status"] == "conflict"
    assert stored_bookings(crm) == []              # nothing for Priya


def test_crm_down_is_honest(crm, tomorrow):
    s, oid = offer(crm, tomorrow)
    chaos(crm, "fail")
    r = create_booking(s, oid)
    assert r["status"] == "failed" and "instruction" in r


def test_double_tap_books_once(crm, tomorrow):
    s, oid = offer(crm, tomorrow)
    first = create_booking(s, oid)
    again = create_booking(s, oid)                 # impatient customer taps again
    assert again.get("booking_id") == first.get("booking_id")
    assert len(stored_bookings(crm)) == 1
