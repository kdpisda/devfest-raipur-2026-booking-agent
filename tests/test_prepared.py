"""Prepared parts (reads, chat loop). These pass on every branch."""
from conftest import make_session

from agent.loop import BookingAgent
from agent.offline import ScriptedClient
from agent.session import Session
from agent.tools import check_availability, lookup_customer


def test_lookup_known_and_unknown(crm):
    s = make_session(crm)
    assert lookup_customer(s)["name"] == "Priya Verma"
    s2 = make_session(crm, phone="+910000000000")
    assert lookup_customer(s2)["status"] == "not_found"


def test_availability_real_prices(crm, tomorrow):
    s = make_session(crm)
    lookup_customer(s)
    r = check_availability(s, tomorrow, "14:00", "16:00", 6)
    sirpur = next(o for o in r["options"] if o["room"] == "Sirpur")
    assert sirpur["price_inr"] == 1280
    assert "Chitrakote" not in [o["room"] for o in r["options"]]


def test_bad_input_is_data(crm):
    s = make_session(crm)
    lookup_customer(s)
    assert check_availability(s, "2001-01-01", "14:00", "16:00", 6)["status"] == "invalid_request"


def test_missing_details_get_a_question(crm):
    agent = BookingAgent(make_session(crm), ScriptedClient())
    assert "how many people" in agent.handle("I need a meeting room tomorrow")


def test_unknown_customer_is_not_booked(crm):
    s = Session(sender_phone="+910000000000", crm_url=crm, confirm=lambda o: True)
    assert "couldn't find" in BookingAgent(s, ScriptedClient()).handle("6 people tomorrow 2-4 pm")
