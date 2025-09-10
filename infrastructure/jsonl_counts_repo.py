import json
from typing import Iterable
from shared.paths import COUNTS_LOG

class JsonlCountsRepo:
    def append(self, row: dict) -> None:
        with COUNTS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row)+"\n")
    def read_range(self, t0: float, t1: float) -> Iterable[dict]:
        with COUNTS_LOG.open("r", encoding="utf-8") as f:
            for line in f:
                try: ev=json.loads(line)
                except: continue
                ts=float(ev.get("ts",0))
                if t0<=ts<=t1: yield ev
