"""STEP 3 · prove_it · pytest tests/test_step3_proof.py"""
import pytest
from conftest import chaos, make_session, stored_bookings
from helpers import offer

from agent.booking import create_booking
from agent.loop import BookingAgent
from agent.offline import ScriptedClient


def test_real_booking_is_verified(crm, tomorrow):
    s, oid = offer(crm, tomorrow)
    r = create_booking(s, oid)
    assert r["status"] == "verified" and r["price_inr"] == 1280
    assert r["booking_id"] in s.verified


@pytest.mark.parametrize("mode,hint", [
    ("ghost", "does not exist"),
    ("wrong_room", "room_id"),
    ("pending", "status"),
])
def test_lies_are_caught(crm, tomorrow, mode, hint):
    s, oid = offer(crm, tomorrow)
    chaos(crm, mode)
    r = create_booking(s, oid)
    assert r["status"] == "not_verified", f"/chaos {mode}: the API said OK but reality differs"
    assert any(hint in p for p in r["problems"]), r["problems"]
    assert not s.verified


def test_ghost_never_reaches_the_customer(crm):
    chaos(crm, "ghost")
    agent = BookingAgent(make_session(crm), ScriptedClient())
    agent.handle("6 people tomorrow 2-4 pm")
    reply = agent.handle("yes")
    assert "BK-" not in reply and "✅" not in reply


def test_timeout_after_write_is_reconciled(crm, tomorrow):
    s, oid = offer(crm, tomorrow)
    chaos(crm, "slow")
    r = create_booking(s, oid)
    assert r["status"] == "verified", r
    assert len(stored_bookings(crm)) == 1
