"""Offline stand-in for Gemini: no Wi-Fi, no API key, no quota? Still workshop.

ScriptedClient mimics `client.models.generate_content(...)` and returns real
google.genai response objects, so loop.py can't tell the difference. It uses
simple rules (regex), which is exactly why we want a real model for messy
language. Use it for setup failures, tests and rehearsals:  python run.py --offline
"""
from __future__ import annotations

import datetime as dt
import itertools
import re

from google.genai import types

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")
_ids = itertools.count(1)

YES = re.compile(r"\b(yes|yeah|yep|ok|okay|sure|confirm|book it|go ahead|haan|ha|theek|done)\b", re.I)
PEOPLE = re.compile(r"(\d+)\s*(people|persons|person|pax|members|log|logon|seats|of us)", re.I)
TIME = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|–|to|se)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje)?", re.I)
ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def _24(h: str, m: str | None, ap: str | None) -> str:
    hh = int(h)
    ap = (ap or "").lower()
    if ap == "pm" and hh < 12:
        hh += 12
    if ap == "am" and hh == 12:
        hh = 0
    if not ap and 1 <= hh <= 7:      # "2-4" in a booking chat almost always means afternoon
        hh += 12
    return f"{hh:02d}:{int(m or 0):02d}"


def extract(text: str) -> dict:
    """Pull date/time/capacity out of the customer's words."""
    out: dict = {}
    today = dt.datetime.now(IST).date()
    low = text.lower()
    if m := ISO.search(text):
        out["date"] = m.group(1)
    elif "day after" in low or "parso" in low:
        out["date"] = (today + dt.timedelta(days=2)).isoformat()
    elif "tomorrow" in low or re.search(r"\bkal\b", low):
        out["date"] = (today + dt.timedelta(days=1)).isoformat()
    elif "today" in low or re.search(r"\baaj\b", low):
        out["date"] = today.isoformat()
    if m := PEOPLE.search(text):
        out["capacity"] = int(m.group(1))
    if m := TIME.search(text):
        ap_end = m.group(6) if (m.group(6) or "").lower() != "baje" else None
        ap_start = m.group(3) or ap_end
        out["start_time"] = _24(m.group(1), m.group(2), ap_start)
        out["end_time"] = _24(m.group(4), m.group(5), ap_end)
    return out


def _call(name: str, **args) -> types.GenerateContentResponse:
    part = types.Part(function_call=types.FunctionCall(name=name, args=args, id=f"call_{next(_ids)}"))
    return _wrap(part)


def _say(text: str) -> types.GenerateContentResponse:
    return _wrap(types.Part(text=text))


def _wrap(part) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[part]))])


def _results(contents) -> list[tuple[str, dict]]:
    out = []
    for c in contents:
        for p in c.parts or []:
            if p.function_response:
                out.append((p.function_response.name, p.function_response.response["result"]))
    return out


class _Models:
    def generate_content(self, model, contents, config=None):
        user_texts = [p.text for c in contents if c.role == "user" for p in (c.parts or []) if p.text]
        last_user = user_texts[-1] if user_texts else ""
        # function results that arrived after the latest customer message
        idx = max(i for i, c in enumerate(contents)
                  if c.role == "user" and any(p.text for p in (c.parts or [])))
        fresh = _results(contents[idx + 1:])
        everything = _results(contents)

        lookups = [r for n, r in everything if n == "lookup_customer"]
        if not lookups:
            return _call("lookup_customer")
        if lookups[-1].get("status") == "not_found":
            return _say("Sorry, I couldn't find an account for this number. "
                        "Our front desk will reach out to help you register.")

        if fresh and fresh[-1][0] == "create_booking":
            r = fresh[-1][1]
            st = r.get("status")
            if st in ("verified", "booked"):
                return _say(f"Done! {r.get('room', 'Your room')} is booked. Reference {r['booking_id']}.")
            if st == "not_confirmed":
                return _say("No problem, I haven't booked anything. Want a different slot?")
            if st == "conflict":
                return _say("Oops, someone just took that slot. Shall I check other options?")
            return _say("I'm sorry, I couldn't confirm the booking. "
                        "Our team will check and get back to you shortly.")

        avail = [r for n, r in everything if n == "check_availability" and r.get("status") == "ok"]
        if YES.search(last_user) and avail and avail[-1]["options"] and not fresh:
            opts = avail[-1]["options"]
            pick = next((o for o in opts if o["room"].lower() in last_user.lower()), opts[0])
            return _call("create_booking", offer_id=pick["offer_id"])

        if fresh and fresh[-1][0] == "check_availability":
            r = fresh[-1][1]
            if r.get("status") != "ok":
                return _say(f"Hmm, that didn't work: {r.get('reason')}. Could you share the details again?")
            if r["options"]:
                o = r["options"][0]
                extra = ""
                if len(r["options"]) > 1:
                    o2 = r["options"][1]
                    extra = f" (Or {o2['room']} for {o2['capacity']} at ₹{o2['price_inr']}.)"
                return _say(f"{o['room']} (seats {o['capacity']}, {o['amenities']}) is free on "
                            f"{o['date']} {o['start_time']}–{o['end_time']} for ₹{o['price_inr']}."
                            f"{extra} Shall I book it?")
            if r["alternatives"]:
                alts = ", ".join(f"{a['room']} {a['start_time']}–{a['end_time']}" for a in r["alternatives"])
                return _say(f"That slot is taken. Nearby options: {alts}. Would one of these work?")
            return _say("Sorry, nothing fits that slot. Want to try another day?")

        slots: dict = {}
        for t in user_texts:
            slots.update(extract(t))
        missing = [k for k in ("date", "start_time", "capacity") if k not in slots]
        if missing:
            ask = {"date": "which day", "start_time": "what time (start and end)",
                   "capacity": "how many people"}
            return _say("Happy to help! Could you tell me " + " and ".join(ask[m] for m in missing) + "?")
        return _call("check_availability", date=slots["date"], start_time=slots["start_time"],
                     end_time=slots["end_time"], capacity=slots["capacity"])


class ScriptedClient:
    def __init__(self):
        self.models = _Models()
