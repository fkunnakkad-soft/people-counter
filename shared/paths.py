from pathlib import Path
from datetime import datetime

APP_NAME   = "People Counter"
APP_DIR    = Path.home() / "people_counter"
DATA_DIR   = APP_DIR / "data"
EV_DIR     = APP_DIR / "events"
CONF_FILE  = APP_DIR / "cameras.jsonl"
COUNTS_LOG = APP_DIR / "counts.jsonl"

KEEP_MIN   = 2  # minutes to keep raw photos

def ensure_dirs():
    for p in [APP_DIR, DATA_DIR, EV_DIR]:
        p.mkdir(parents=True, exist_ok=True)
    if not CONF_FILE.exists():
        CONF_FILE.write_text("", encoding="utf-8")
    if not COUNTS_LOG.exists():
        COUNTS_LOG.write_text("", encoding="utf-8")

def fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
