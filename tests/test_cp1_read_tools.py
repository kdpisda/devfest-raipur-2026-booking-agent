"""CHECKPOINT 1 · pytest tests/test_cp1_read_tools.py"""
from conftest import make_session

from agent.declarations import TOOL_DECLARATIONS
from agent.tools import check_availability, lookup_customer


def test_check_availability_is_declared():
    decl = next((d for d in TOOL_DECLARATIONS if d and d.get("name") == "check_availability"), None)
    assert decl, "add a check_availability declaration to TOOL_DECLARATIONS"
    props = decl["parameters"]["properties"]
    for f in ("date", "start_time", "end_time", "capacity"):
        assert f in props, f"declaration is missing parameter {f!r}"
    assert set(decl["parameters"]["required"]) >= {"date", "start_time", "end_time", "capacity"}
    assert props["capacity"]["type"] == "integer"


def test_lookup_known_customer(crm):
    s = make_session(crm)
    r = lookup_customer(s)
    assert r["status"] == "found" and r["name"] == "Priya Verma"
    assert s.customer and s.customer["id"] == "C-101", "store the CRM record on the session"


def test_lookup_unknown_customer(crm):
    s = make_session(crm, phone="+910000000000")
    r = lookup_customer(s)
    assert r["status"] == "not_found"
    assert s.customer is None


def test_availability_returns_real_options(crm, tomorrow):
    s = make_session(crm)
    lookup_customer(s)
    r = check_availability(s, tomorrow, "14:00", "16:00", 6)
    assert r["status"] == "ok"
    rooms = [o["room"] for o in r["options"]]
    assert "Chitrakote" not in rooms, "Chitrakote is already booked tomorrow afternoon"
    assert "Sirpur" in rooms
    sirpur = next(o for o in r["options"] if o["room"] == "Sirpur")
    assert sirpur["price_inr"] == 1280, "price must come from the CRM (member gets 20% off)"
    assert sirpur["offer_id"] in s.offers, "remember offers you showed in s.offers"


def test_availability_bad_input_is_data_not_crash(crm):
    s = make_session(crm)
    lookup_customer(s)
    r = check_availability(s, "2001-01-01", "14:00", "16:00", 6)
    assert r["status"] == "invalid_request" and "past" in r["reason"]


def test_availability_requires_lookup_first(crm, tomorrow):
    s = make_session(crm)
    r = check_availability(s, tomorrow, "14:00", "16:00", 6)
    assert r["status"] == "error"
