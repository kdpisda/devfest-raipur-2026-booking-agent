"""Chat with your booking agent.

    python run.py                    # real Gemini (needs GEMINI_API_KEY)
    python run.py --offline          # no internet / no key: scripted stand-in model
    python run.py --naive            # the "Booked! (not really)" villain, for comparison
    python run.py --from +919800000002   # message as a different customer

In the chat:  /chaos ghost | wrong_room | pending | fail | slow | none
              /reset   /board   /quit
Open the CRM board in a browser to see what is REALLY stored.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PORT = int(os.environ.get("CRM_PORT", "8765"))
CRM = f"http://127.0.0.1:{PORT}"

DIM, B, G, R, Y, C, X = "\033[2m", "\033[1m", "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[0m"
if os.name == "nt":
    os.system("")  # enable ANSI colours on Windows terminals


def load_dotenv() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def start_crm() -> None:
    try:
        if httpx.get(f"{CRM}/health", timeout=0.5).status_code == 200:
            return  # already running (e.g. another terminal)
    except httpx.HTTPError:
        pass
    import uvicorn
    from crm.app import app, reset_db

    reset_db()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            if httpx.get(f"{CRM}/health", timeout=0.3).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.1)
    sys.exit("CRM did not start. Is port %d busy? Try: CRM_PORT=8877 python run.py" % PORT)


def confirm_button(offer: dict) -> bool:
    print(f"\n{Y}┌─ WhatsApp confirmation ─────────────────────────────")
    print(f"│ {offer['room']} · {offer['date']} · {offer['start_time']}–{offer['end_time']}")
    print(f"│ ₹{offer['price_inr']}  (seats {offer['capacity']})")
    print(f"└──────────────────────────────────── [Confirm] [Cancel]{X}")
    return input(f"{Y}Tap Confirm? (y/N): {X}").strip().lower() in ("y", "yes")


def on_event(kind: str, data: dict) -> None:
    from agent.loop import pretty
    if kind == "call":
        print(f"{DIM}  ⚙  {data['name']}({pretty(data['args'])}){X}")
    elif kind == "result":
        res = data["result"]
        col = G if res.get("status") in ("found", "ok", "verified") else (R if res.get("status") in (
            "failed", "not_verified", "unknown", "error", "rejected") else DIM)
        text = pretty(res)
        print(f"{col}  ↳  {text[:300]}{'…' if len(text) > 300 else ''}{X}")
    elif kind == "guard":
        print(f"{R}  🛑 truth guard blocked unverified reference(s): {data['blocked']}{X}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="scripted model, no API calls")
    ap.add_argument("--naive", action="store_true", help="no confirmation, no verification")
    ap.add_argument("--from", dest="sender", default="+919800000001", help="customer phone")
    ap.add_argument("--chaos", default="none")
    a = ap.parse_args()

    load_dotenv()
    if not a.offline and not os.environ.get("GEMINI_API_KEY"):
        sys.exit(f"{R}No GEMINI_API_KEY. Get one at https://aistudio.google.com/apikey, put it in "
                 f".env, or run with --offline.{X}")

    start_crm()
    httpx.post(f"{CRM}/admin/chaos", json={"mode": a.chaos})

    from agent.loop import MODEL, BookingAgent, make_client
    from agent.session import Session

    s = Session(sender_phone=a.sender, crm_url=CRM, confirm=confirm_button, naive=a.naive)
    agent = BookingAgent(s, make_client(a.offline), on_event=on_event)

    mode = "offline script" if a.offline else MODEL
    print(f"{B}☕ Chai & Code Cowork booking agent{X}  {DIM}[{mode}{', NAIVE' if a.naive else ''}]{X}")
    print(f"{DIM}CRM board: {CRM}/   ·  you are messaging from {a.sender}  ·  /quit to exit{X}\n")

    while True:
        try:
            msg = input(f"{C}customer ▸ {X}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not msg:
            continue
        if msg in ("/quit", "/exit"):
            break
        if msg.startswith("/chaos"):
            mode_ = (msg.split() + ["none"])[1]
            print(DIM + httpx.post(f"{CRM}/admin/chaos", json={"mode": mode_}).text + X)
            continue
        if msg == "/reset":
            httpx.post(f"{CRM}/admin/reset")
            s.offers.clear(); s.verified.clear(); s.customer = None
            agent.history.clear()
            print(f"{DIM}CRM reset, conversation cleared.{X}")
            continue
        if msg == "/board":
            print(f"{DIM}{CRM}/{X}")
            continue
        try:
            reply = agent.handle(msg)
        except Exception as e:  # keep the room moving even if the API hiccups
            reply = f"{R}[agent error: {type(e).__name__}: {str(e)[:200]}]{X}"
        print(f"{B}agent ▸{X} {reply}\n")


if __name__ == "__main__":
    main()
