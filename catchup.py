"""Fell behind? No shame. Jump to a checkpoint (overwrites agent/declarations.py,
agent/tools.py and agent/verify.py; your old versions are saved as *.mine.py).

    python catchup.py 1      # read tools done (declaration, lookup, availability)
    python catchup.py 2      # + create_booking with the confirmation gate
    python catchup.py 3      # + verification  (= full reference solution)
    python catchup.py start  # back to the empty starter
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ("declarations.py", "tools.py", "verify.py")

if len(sys.argv) != 2 or sys.argv[1] not in ("1", "2", "3", "start"):
    sys.exit(__doc__)
name = "start" if sys.argv[1] == "start" else f"cp{sys.argv[1]}"
for f in FILES:
    mine = ROOT / "agent" / f
    if mine.exists():
        shutil.copy(mine, mine.with_suffix(".mine.py"))
    shutil.copy(ROOT / "checkpoints" / name / "agent" / f, mine)
print(f"✔ agent/ is now at checkpoint {sys.argv[1]}. Your previous files are agent/*.mine.py")
