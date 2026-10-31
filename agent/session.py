"""Per-conversation state that belongs to the APPLICATION, not to the model.

Gemini never gets to choose who the customer is, which offers exist, or
whether something was verified. Those facts live here, in Python.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import httpx


@dataclass
class Session:
    sender_phone: str                      # trusted: comes from the channel (WhatsApp/SMS), not the model
    crm_url: str = "http://127.0.0.1:8765"
    confirm: Callable[[dict], bool] = lambda offer: False   # the "Confirm" button
    naive: bool = False                    # demo mode: no confirmation gate, no verification

    customer: dict | None = None           # filled by lookup_customer
    offers: dict[str, dict] = field(default_factory=dict)   # offer_id -> offer we actually showed
    verified: dict[str, dict] = field(default_factory=dict) # booking_id -> verified record
    trace: list[str] = field(default_factory=list)

    def http(self) -> httpx.Client:
        # Short timeout on purpose: real APIs are slow, and we must handle it.
        return httpx.Client(base_url=self.crm_url, timeout=3.0)

    def log(self, line: str) -> None:
        self.trace.append(line)
