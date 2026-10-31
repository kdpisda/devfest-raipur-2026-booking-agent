"""STEP 2 · pytest tests/test_step2_write.py"""
from conftest import chaos, make_session, stored_bookings

from agent.tools import check_availability, create_booking, lookup_customer


def _offer(crm, tomorrow, room="Sirpur", phone="+919800000001", confirm=True):
    s = make_session(crm, phone=phone, confirm=confirm)
    lookup_customer(s)
    r = check_availability(s, tomorrow, "14:00", "16:00", 6)
    return s, next(o for o in r["options"] if o["room"] == room)["offer_id"]


def test_no_confirm_no_write(crm, tomorrow):
    s, oid = _offer(crm, tomorrow, confirm=False)
    r = create_booking(s, oid)
    assert r["status"] == "not_confirmed"
    assert stored_bookings(crm) == [], "nothing may be written without Confirm"


def test_confirmed_booking_is_persisted_once(crm, tomorrow):
    s, oid = _offer(crm, tomorrow)
    r = create_booking(s, oid)
    assert r.get("booking_id"), r
    rows = stored_bookings(crm)
    assert len(rows) == 1
    assert rows[0]["room_id"] == "R-SIR" and rows[0]["start_time"] == "14:00"


def test_model_cannot_invent_offers(crm, tomorrow):
    s, _ = _offer(crm, tomorrow)
    r = create_booking(s, "OF-MADEUP")
    assert r["status"] == "rejected"
    assert stored_bookings(crm) == []


def test_conflict_is_reported(crm, tomorrow):
    s1, oid1 = _offer(crm, tomorrow)
    s2, oid2 = _offer(crm, tomorrow, phone="+919800000002")
    assert create_booking(s2, oid2).get("booking_id")      # Arjun grabs Sirpur first
    r = create_booking(s1, oid1)
    assert r["status"] == "conflict"
    assert stored_bookings(crm) == []


def test_api_failure_is_not_success(crm, tomorrow):
    s, oid = _offer(crm, tomorrow)
    chaos(crm, "fail")
    r = create_booking(s, oid)
    assert r["status"] == "failed"
    assert "instruction" in r
