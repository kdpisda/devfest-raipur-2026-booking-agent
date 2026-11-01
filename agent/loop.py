"""The agent loop: Gemini proposes, Python disposes.

    customer msg -> Gemini -> (function_call?) -> Python runs tool -> result -> Gemini -> ... -> reply

This file is prepared for you. Read it; today you only edit booking.py.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

from google.genai import types

from .declarations import TOOL_DECLARATIONS
from .session import Session
from .tools import dispatch

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
MAX_STEPS = 8          # a loop without a ceiling is a bill without a ceiling
REF = re.compile(r"\bBK-[A-Z0-9]{4,}\b")


def system_prompt() -> str:
    now = dt.datetime.now(IST)
    return f"""You are the WhatsApp booking assistant for Chai & Code Cowork, Raipur.
Today is {now:%A, %d %B %Y}, current time {now:%H:%M} IST. All times are IST.

How to work:
- First call lookup_customer. If not found, politely say we couldn't find their account and
  that the front desk will help; do not book.
- You need date, start time, end time and number of people. If any is missing or ambiguous,
  ask a short clarifying question. Never guess.
- Use check_availability. Quote rooms and prices exactly as returned. Never invent prices.
- Offer one option (mention one alternative if useful) and ask the customer to confirm.
- Only after they agree to that specific option, call create_booking with its offer_id.
- A booking is done ONLY if create_booking returns status "verified". For any other status,
  say honestly that it is not confirmed yet. Never make up a booking reference.
- Customers may write in English, Hindi or Hinglish. Reply in the same style. Keep replies short.
"""


def build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=system_prompt(),
        tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
        # We run tools ourselves, so we can gate, log and verify them.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


class BookingAgent:
    def __init__(self, session: Session, client, model: str = MODEL, on_event=None):
        self.s = session
        self.client = client
        self.model = model
        self.history: list[types.Content] = []
        self.on_event = on_event or (lambda kind, data: None)

    def handle(self, user_text: str) -> str:
        self.history.append(types.Content(role="user", parts=[types.Part(text=user_text)]))
        verified_before = set(self.s.verified)

        for _ in range(MAX_STEPS):
            resp = self.client.models.generate_content(
                model=self.model, contents=self.history, config=build_config())
            if not resp.candidates or resp.candidates[0].content is None:
                return "Sorry, I couldn't process that. Could you rephrase?"
            # Keep the model's turn exactly as returned (it carries thought signatures).
            self.history.append(resp.candidates[0].content)

            calls = resp.function_calls or []
            if not calls:
                reply = resp.text or ""
                return self._truth_guard(reply, verified_before)

            parts = []
            for call in calls:
                args = dict(call.args or {})
                self.on_event("call", {"name": call.name, "args": args})
                result = dispatch(self.s, call.name, args)
                self.on_event("result", {"name": call.name, "result": result})
                parts.append(types.Part(function_response=types.FunctionResponse(
                    id=call.id, name=call.name, response={"result": result})))
            self.history.append(types.Content(role="user", parts=parts))

        return "Sorry, I couldn't finish that safely. A team member will follow up shortly."

    # ------------------------------------------------------------------
    def _truth_guard(self, reply: str, verified_before: set[str]) -> str:
        """Last line of defence: the model may not mention references we never verified."""
        if self.s.naive:
            return reply
        claimed = set(REF.findall(reply))
        fake = claimed - set(self.s.verified)
        if fake:
            self.on_event("guard", {"blocked": sorted(fake)})
            return ("I'm sorry, I can't confirm a booking right now. Our team will check "
                    "and message you shortly.")
        new = [b for b in self.s.verified if b not in verified_before]
        if new:  # the receipt comes from verified data, not from the model's prose
            b = self.s.verified[new[-1]]
            reply += (f"\n\n✅ Verified in CRM: {b['id']} · {b['room']} · {b['date']} "
                      f"{b['start_time']}–{b['end_time']} · ₹{b['price_inr']}")
        return reply


def make_client(offline: bool):
    if offline:
        from .offline import ScriptedClient
        return ScriptedClient()
    from google import genai
    return genai.Client()   # reads GEMINI_API_KEY from the environment


def pretty(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
