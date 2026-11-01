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
git checkout step-1          # where the hands-on starts
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

## The story

Sharma ji runs **Chai & Code Cowork** in Raipur. Over the weekend his beta "shipped" an AI receptionist
on WhatsApp. On Monday it told Priya her meeting room was booked. On Tuesday at 2 PM, Priya and five
colleagues walked in. There was no booking. Today we rebuild that agent, in three steps, so it never
says "booked" unless it really booked. (Everyone in this story is fictional.)

## You edit ONE file: `agent/booking.py`

Everything else (the Gemini loop, the read tools, the CRM) is prepared. `agent/booking.py` is
Sharma ji's beta's code. It *runs*, and it is wrong in three ways. Each step fixes one function:

| Step | Function | The beta's bug | Branch to start | Check yourself | Stuck? |
|------|----------|----------------|-----------------|----------------|--------|
| 1 | `check_approval` | books without the customer tapping Confirm, books offers the model made up | `step-1` | `pytest tests/test_step1_approval.py` | `git checkout step-1-solution` |
| 2 | `write_booking` | crashes when the CRM says no, no Idempotency-Key | `step-2` | `pytest tests/test_step2_write.py` | `git checkout step-2-solution` |
| 3 | `prove_it` | believes the API, prints a receipt for a booking that doesn't exist | `step-3` | `pytest tests/test_step3_proof.py` | `git checkout step-3-solution` |

Switching branches with unfinished edits? `git stash` first. See a solution: `git diff step-1..step-1-solution`.

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
