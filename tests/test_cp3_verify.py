"""CHECKPOINT 3 · pytest tests/test_cp3_verify.py"""
import pytest
from conftest import chaos, make_session, stored_bookings

from agent.loop import BookingAgent
from agent.offline import ScriptedClient
from agent.tools import check_availability, create_booking, lookup_customer


def _offer(crm, tomorrow):
    s = make_session(crm)
    lookup_customer(s)
    r = check_availability(s, tomorrow, "14:00", "16:00", 6)
    return s, next(o for o in r["options"] if o["room"] == "Sirpur")["offer_id"]


def test_happy_path_is_verified(crm, tomorrow):
    s, oid = _offer(crm, tomorrow)
    r = create_booking(s, oid)
    assert r["status"] == "verified", r
    assert r["booking_id"] in s.verified


@pytest.mark.parametrize("mode,hint", [
    ("ghost", "does not exist"),
    ("wrong_room", "room_id"),
    ("pending", "status"),
])
def test_lies_are_caught(crm, tomorrow, mode, hint):
    s, oid = _offer(crm, tomorrow)
    chaos(crm, mode)
    r = create_booking(s, oid)
    assert r["status"] == "not_verified", f"{mode}: the API said OK but reality differs"
    assert any(hint in p for p in r["problems"]), r["problems"]
    assert not s.verified


def _chat(crm, msgs):
    s = make_session(crm)
    agent = BookingAgent(s, ScriptedClient())
    return [agent.handle(m) for m in msgs], s


def test_end_to_end_success_has_receipt(crm):
    replies, s = _chat(crm, ["Hi, meeting room for 6 people tomorrow 2-4 pm?", "yes please"])
    assert "Sirpur" in replies[0] and "₹1280" in replies[0]
    assert "✅ Verified in CRM" in replies[1]
    assert len(stored_bookings(crm)) == 1


def test_end_to_end_ghost_never_claims_success(crm):
    chaos(crm, "ghost")
    replies, s = _chat(crm, ["6 people tomorrow 2-4 pm", "yes"])
    assert "BK-" not in replies[1] and "✅" not in replies[1]
    assert stored_bookings(crm) == []


def test_missing_details_get_a_question(crm):
    replies, _ = _chat(crm, ["I need a meeting room tomorrow"])
    assert "?" in replies[0] and "how many people" in replies[0]


def test_unknown_customer_is_not_booked(crm):
    from agent.session import Session
    s = Session(sender_phone="+910000000000", crm_url=crm, confirm=lambda o: True)
    agent = BookingAgent(s, ScriptedClient())
    assert "couldn't find" in agent.handle("6 people tomorrow 2-4 pm")
