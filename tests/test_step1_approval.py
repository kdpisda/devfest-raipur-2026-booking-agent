"""STEP 1 · check_approval · pytest tests/test_step1_approval.py"""
from conftest import stored_bookings
from helpers import offer

from agent.booking import create_booking


def test_no_confirm_no_write(crm, tomorrow):
    s, oid = offer(crm, tomorrow, confirm=False)
    r = create_booking(s, oid)
    assert r["status"] == "not_confirmed"
    assert stored_bookings(crm) == [], "nothing may be written without the Confirm tap"


def test_model_cannot_invent_offers(crm, tomorrow):
    s, _ = offer(crm, tomorrow)
    r = create_booking(s, "OF-MADEUP")
    assert r["status"] == "rejected"
    assert stored_bookings(crm) == []


def test_confirmed_offer_is_written(crm, tomorrow):
    s, oid = offer(crm, tomorrow)
    create_booking(s, oid)
    rows = stored_bookings(crm)
    assert len(rows) == 1 and rows[0]["room_id"] == "R-SIR"
