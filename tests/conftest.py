import datetime as dt
import socket
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crm.app import app, reset_db  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def crm_url():
    import uvicorn
    port = _free_port()
    reset_db()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            httpx.get(url + "/health", timeout=0.2)
            break
        except httpx.HTTPError:
            time.sleep(0.05)
    yield url
    server.should_exit = True


@pytest.fixture
def crm(crm_url):
    httpx.post(crm_url + "/admin/reset")
    yield crm_url
    httpx.post(crm_url + "/admin/chaos", json={"mode": "none"})


@pytest.fixture
def tomorrow():
    return (dt.datetime.now(IST).date() + dt.timedelta(days=1)).isoformat()


def make_session(crm, phone="+919800000001", confirm=True):
    from agent.session import Session
    return Session(sender_phone=phone, crm_url=crm, confirm=lambda offer: confirm)


def chaos(crm, mode):
    httpx.post(crm + "/admin/chaos", json={"mode": mode}).raise_for_status()


def stored_bookings(crm, customer_id="C-101"):
    return httpx.get(crm + "/bookings", params={"customer_id": customer_id}).json()
