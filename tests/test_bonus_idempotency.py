"""BONUS · timeouts after a successful write. pytest tests/test_bonus_idempotency.py"""
from conftest import chaos, make_session, stored_bookings

from agent.tools import check_availability, create_booking, lookup_customer


def test_timeout_is_reconciled_without_duplicates(crm, tomorrow):
    s = make_session(crm)
    lookup_customer(s)
    oid = next(o for o in check_availability(s, tomorrow, "14:00", "16:00", 6)["options"]
               if o["room"] == "Sirpur")["offer_id"]
    chaos(crm, "slow")
    r = create_booking(s, oid)
    assert r["status"] == "verified", r
    chaos(crm, "none")
    again = create_booking(s, oid)          # an impatient retry
    assert again["booking_id"] == r["booking_id"]
    assert len(stored_bookings(crm)) == 1
