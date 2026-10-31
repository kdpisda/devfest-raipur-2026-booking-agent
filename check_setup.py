"""Run this BEFORE the session:  python check_setup.py

Checks Python, packages, your Gemini API key and one tiny real model call.
"""
import importlib
import os
import sys
from pathlib import Path

ok = True


def line(good, msg, fix=""):
    global ok
    ok &= good
    print(("✅ " if good else "❌ ") + msg + ("" if good else f"\n     → {fix}"))


line(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "install Python 3.10+")
for mod in ("google.genai", "fastapi", "uvicorn", "httpx", "pytest"):
    try:
        importlib.import_module(mod)
        line(True, f"package {mod}")
    except ImportError:
        line(False, f"package {mod}", "pip install -r requirements.txt")

env = Path(__file__).with_name(".env")
if env.exists():
    for l in env.read_text().splitlines():
        if "=" in l and not l.startswith("#"):
            k, v = l.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

key = os.environ.get("GEMINI_API_KEY", "")
line(bool(key), "GEMINI_API_KEY found",
     "create one at https://aistudio.google.com/apikey and put GEMINI_API_KEY=... in .env")

if key:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    try:
        from google import genai
        r = genai.Client().models.generate_content(model=model, contents="Reply with just: ready")
        line(True, f"Gemini answered via {model}: {(r.text or '').strip()[:40]}")
    except Exception as e:
        line(False, f"Gemini call failed: {type(e).__name__}: {str(e)[:160]}",
             "check the key / network. Try GEMINI_MODEL=gemini-3.5-flash-lite. "
             "Worst case: python run.py --offline")

print("\nAll set. See you at DevFest Raipur! 🎉" if ok else
      "\nSome checks failed. You can still follow along with:  python run.py --offline")
