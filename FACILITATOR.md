# Facilitator guide

Session: **Did the AI actually book it?** · DevFest Raipur 2026 · KD
Audience: students + working developers. Format: short concepts, long hands-on, short career talk.

## DevFest Raipur 2026 slot: 3:30–4:30 PM (60 min, right after lunch)

| Clock | Block |
|---|---|
| 3:30–3:36 | Hook: post-lunch meme, intro, naive demo, ghost booking |
| 3:36–3:42 | Concepts (fncall + boundary slides are 60 seconds each) |
| 3:42–3:57 | **CP1** as a live code-along · `catchup.py 1` at 3:57 for everyone |
| 3:57–4:07 | **CP2** · `catchup.py 2` at 4:07 |
| 4:07–4:20 | **CP3** + chaos modes (never cut) |
| 4:20–4:26 | Career: students, then professionals |
| 4:26–4:30 | Rules slide, Q&A, hard stop |

## Pick your run sheet

The slot is "an hour and more", so here are three versions. Minutes are from the start of *your* session,
not the event opening. Verification (Checkpoint 3) is never cut.

| Block | 60 min | 75 min | 90 min |
|---|---|---|---|
| Hook + naive demo ("Booked!" with an empty CRM) | 0–6 | 0–8 | 0–10 |
| Concepts: architecture, function calling, model vs app | 6–12 | 8–16 | 10–20 |
| **CP1** · TODO 1–3 · read tools | 12–27 | 16–34 | 20–45 |
| **CP2** · TODO 4 · confirm + write | 27–37 | 34–47 | 45–60 |
| **CP3** · TODO 5 · read-back verification + chaos modes | 37–50 | 47–63 | 60–75 |
| Career guidance | 50–56 | 63–70 | 75–85 |
| Q&A, repo link | 56–60 | 70–75 | 85–90 |

**60-minute version, what to cut:** skip the `fncall` and `boundary` slides (say them in one sentence each),
do CP1 as a live code-along on the projector instead of solo work, and have everyone run
`python catchup.py 1` at minute 27 no matter what. Bonus (idempotency) is a "try at home".

## Before the session

- Share the repo link 1–2 days ahead with: *"Run `python check_setup.py` before you come."*
- T-15 min: projector, mic, Wi-Fi, and a smoke test: `python run.py --offline` and open `http://127.0.0.1:8765/`.
- Have two terminals ready: `python run.py --offline` (good agent) and
  `CRM_PORT=8790 python run.py --offline --naive --chaos ghost` (the villain).

## Catch-up checkpoints

| When | Command | Gives them |
|---|---|---|
| CP1 deadline | `python catchup.py 1` | declaration + lookup + availability |
| CP2 deadline | `python catchup.py 2` | + create_booking with Confirm gate |
| End | `python catchup.py 3` | full reference (everything verified) |

Their own work is saved as `agent/*.mine.py`. Nothing is lost.

## When things break

| Problem | Fix |
|---|---|
| No API key / quota / 429 | `python run.py --offline`, or `GEMINI_MODEL=gemini-3.5-flash-lite` in `.env` |
| Wi-Fi is down | `--offline` needs no internet at all (only `pip install` does) |
| Port 8765 busy | `CRM_PORT=8877 python run.py` |
| No laptop | pair up, or Colab (see README) |
| Python < 3.10 | Colab |

## Demo script (hook)

1. Villain terminal: `6 people tomorrow 2-4 pm` → `yes` → agent says **"Done! Booked."**
2. Point at the CRM board: no new row. *"Whose fault is this? The model faithfully repeated what the API said."*
3. Good terminal, same chat, `/chaos ghost`: agent refuses to claim success. *"That's what we build today."*

## Acceptance checks (all covered by `pytest tests`)

- Confirmed → exactly one booking for the right customer, room and time, and the reply carries the verified reference.
- No Confirm → no write.
- Slot taken → conflict, no success claim.
- Missing details → a clarifying question.
- API failure, ghost write, wrong room, pending status → never "booked".
- Timeout after write → reconciled by idempotency key, no duplicate (bonus).
