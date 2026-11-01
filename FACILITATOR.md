# Facilitator guide

Session: **Did the AI actually book it?** · DevFest Raipur 2026 · KD
Slot: **3:30–4:30 PM (60 min, right after lunch)**. Audience: students + working developers.

## The story (tell it, don't read it)

1. **The hire.** Sharma ji runs Chai & Code Cowork in Raipur. His beta ships an AI receptionist on WhatsApp over the weekend. Very proud.
2. **The disaster.** Priya books a room for six on WhatsApp. "Done! Booked." Next day at 2 PM, six people walk in. No booking. Sharma ji is not proud.
3. **The investigation.** Whose fault? (audience vote). The API lied, and nobody checked.
4. **The rebuild.** Attendees inherit the beta's `agent/booking.py` and fix it in three functions: ask first (`check_approval`), write once and honestly (`write_booking`), read it back (`prove_it`).
5. **Chaos week.** The audience picks how the CRM lies next. The agent has to stay honest.
6. **Happy ending.** Receipts printed from verified data. Career: how to turn this into proof of skill.

## Run sheet

| Clock | Block | Branch on screen |
|---|---|---|
| 3:30–3:42 | Story chapters 1–3, naive demo, hands-up + whose-fault poll, concepts | `main` |
| 3:42–3:44 | Setup check: everyone on `step-1`, `python run.py --offline` works | `step-1` |
| 3:44–3:55 | **Step 1** `check_approval`: bug demo, code from the slide, run | `step-1` → present `step-1-solution` |
| 3:55–4:05 | **Step 2** `write_booking`; at 4:05 everyone `git stash && git checkout step-3` | `step-2` → present `step-2-solution` |
| 4:05–4:18 | **Step 3** `prove_it` + predict-the-output + audience-picks-the-chaos | `step-3` → present `step-3-solution` |
| 4:18–4:25 | Happy ending, career (students, then professionals) | `step-3-solution` |
| 4:25–4:30 | Rules, feedback (keep / fix), Q&A, hard stop | |

## Presenting a solution branch

You don't need an editor: every step's bug, code, commands and expected output are on the slides.
The commands below are only if you want to show them live.

```bash
git stash && git checkout step-1-solution
git diff step-1..step-1-solution          # the whole solution, nothing else
pytest tests/test_step1_approval.py -q
python run.py --offline                   # "6 people tomorrow 2-4 pm"
```

Then everyone moves on together: `git stash && git checkout step-2`.

## Audience moments (make them talk)

| When | Prompt | What you're fishing for |
|---|---|---|
| After the cover | Hands up: built a chatbot? It ever *did* something? Checked it really happened? | Hands drop at the third question |
| After the disaster | Whose fault? A) Gemini B) Sharma ji's beta C) the API D) nobody checked | Everyone is a bit right; D is the lesson |
| Model vs app slide | What else should never be the model's decision? | Refunds, discounts, deleting data, sending money |
| Before step 3 | Ghost mode is on. What will your agent say now? | "Not confirmed yet" once verify works |
| Chaos slide | What could go wrong with a booking API? Then: you pick the chaos mode | Map their answers onto ghost / wrong_room / pending / fail / slow |
| Feedback slide | One thing to keep, one thing to fix | Shout-outs, or the feedback form |

## Before the session

- Repo must be **public**. Share the link a day ahead: *"Run `python check_setup.py` and `git checkout step-1` before you come."*
- T-15 min: projector, mic, Wi-Fi, smoke test: `python run.py --offline` and open `http://127.0.0.1:8765/`.
- Two terminals ready: `python run.py --offline` (good agent) and
  `CRM_PORT=8790 python run.py --offline --naive --chaos ghost` (the villain).

## When things break

| Problem | Fix |
|---|---|
| Local edits block `git checkout` | `git stash` first (or `git checkout -f step-N` to throw them away) |
| No API key / quota / 429 | `python run.py --offline`, or `GEMINI_MODEL=gemini-3.5-flash-lite` in `.env` |
| Wi-Fi is down | `--offline` needs no internet (only `pip install` and `git clone` do) |
| Port 8765 busy | `CRM_PORT=8877 python run.py` |
| No laptop | pair up, or Colab (see README) |

## Acceptance checks (all covered by `pytest tests` on `step-3-solution`)

- Confirmed → exactly one booking for the right customer, room and time, and the reply carries the verified reference.
- No Confirm → no write. Slot taken → conflict, no success claim. Missing details → a clarifying question.
- API failure, ghost write, wrong room, pending status → never "booked".
- Timeout after write → reconciled by idempotency key, no duplicate (bonus).
