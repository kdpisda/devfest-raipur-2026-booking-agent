from conftest import make_session

from agent.tools import check_availability, lookup_customer


def offer(crm, tomorrow, room="Sirpur", phone="+919800000001", confirm=True):
    s = make_session(crm, phone=phone, confirm=confirm)
    lookup_customer(s)
    r = check_availability(s, tomorrow, "14:00", "16:00", 6)
    return s, next(o for o in r["options"] if o["room"] == room)["offer_id"]
