# Did the AI actually book it? 🤔

**Beyond Chatbots: build a customer booking agent with Gemini**
Hands-on workshop · DevFest Raipur 2026 · Kuldeep Pisda (KD)

A customer messages *Chai & Code Cowork, Raipur*:

> Hi, I need a meeting room for six people tomorrow, 2–4 PM. What's available?

Your agent will look the customer up in a CRM, check real availability and prices, get an explicit
confirmation, create the booking, **read it back to prove it exists**, and only then say "booked".

```
customer msg ─► Gemini ─► function_call ─► Python tool ─► CRM API
                  ▲                                         │
                  └──────── function_response ◄─────────────┘
                                  │
                       verify: read the record back
                                  │
                 reply built from VERIFIED data only ✅
```

## Setup (do this before the session, ~10 min)

```bash
git clone https://github.com/kdpisda/devfest-raipur-2026-booking-agent && cd devfest-raipur-2026-booking-agent
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # paste your key from https://aistudio.google.com/apikey
python check_setup.py
```

No laptop setup? Open a [Colab](https://colab.research.google.com) notebook and run
`!git clone https://github.com/kdpisda/devfest-raipur-2026-booking-agent`, `%cd devfest-raipur-2026-booking-agent`, `!pip install -q -r requirements.txt`,
then `import os; os.environ["GEMINI_API_KEY"]="..."` and `!python run.py`.

No internet or key on the day? Everything works with `--offline` (a scripted stand-in model).

Facilitating? See [FACILITATOR.md](FACILITATOR.md) for 60 / 75 / 90-minute run sheets.

## Run it

```bash
python run.py              # chat with your agent (real Gemini)
python run.py --offline    # same app, scripted model, no API calls
python run.py --naive      # the villain: no confirmation, no verification
```

Open **http://127.0.0.1:8765/** for the CRM board: what is *really* in the database.

Chat commands: `/chaos ghost|wrong_room|pending|fail|slow|none`, `/reset`, `/quit`.

## What you build

| # | File | TODO | Checkpoint test |
|---|------|------|-----------------|
| 1 | `agent/declarations.py` | declare `check_availability` | `pytest tests/test_cp1_read_tools.py` |
| 2 | `agent/tools.py` | `lookup_customer` | 〃 |
| 3 | `agent/tools.py` | `check_availability` | 〃 |
| 4 | `agent/tools.py` | `create_booking` + the Confirm gate | `pytest tests/test_cp2_booking.py` |
| 5 | `agent/verify.py` | `verify_booking` read-back | `pytest tests/test_cp3_verify.py` |
| ★ | already in `tools.py` | timeouts + idempotency | `pytest tests/test_bonus_idempotency.py` |

Behind? `python catchup.py 1` (or 2, 3). Your work is saved as `agent/*.mine.py`.

## Chaos modes (the CRM lies to you on purpose)

| mode | what the API says | what's actually stored |
|------|-------------------|------------------------|
| `ghost` | 201 Created ✅ | nothing |
| `wrong_room` | your room ✅ | a different room |
| `pending` | confirmed ✅ | `pending_payment` |
| `fail` | 503 | nothing |
| `slow` | (times out) | the booking, after 6s |

## The rules this repo encodes

1. **The model proposes, the application disposes.** Gemini picks tools; Python enforces business rules.
2. **Identity comes from the channel**, never from a model-chosen ID.
3. **Prices come from the system of record**, never from the model.
4. **Writes need explicit confirmation** of the exact thing being written.
5. **A 200 is not proof. Read it back.** Only a matching, confirmed record means "booked".
6. **Unknown ≠ failed ≠ success.** Say what you know; reconcile before retrying.

## Stack

Python · [Google Gen AI SDK](https://googleapis.github.io/python-genai/) (`google-genai`) with
manual function calling · Gemini (`gemini-3.8-flash` by default, override with `GEMINI_MODEL`) ·
FastAPI + SQLite fake CRM. All customer data is fictional.
