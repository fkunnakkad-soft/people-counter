import shutil, time
from datetime import datetime
from shared.paths import EV_DIR

class LocalImageStore:
    def move_and_stamp(self, tmp_path: str, remote_ip: str, raw_name: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dest = EV_DIR / f"{stamp}__{raw_name}"
        shutil.move(tmp_path, dest); return str(dest)
    def purge_older_than(self, seconds: float) -> int:
        cutoff = time.time() - seconds; n=0
        for p in EV_DIR.glob("*.jpg"):
            try:
                if p.stat().st_mtime < cutoff: p.unlink(missing_ok=True); n+=1
            except: pass
        return n
