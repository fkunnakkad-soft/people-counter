import json
from typing import List
from domain.models import CameraConf
from shared.paths import CONF_FILE

class JsonlCameraRepo:
    def load_all(self) -> List[CameraConf]:
        out: List[CameraConf] = []
        with CONF_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try: out.append(CameraConf.from_dict(json.loads(line)))
                except: pass
        return out
    def save_all(self, items: List[CameraConf]) -> None:
        tmp = CONF_FILE.with_suffix(".new")
        with tmp.open("w", encoding="utf-8") as f:
            for c in items: f.write(json.dumps(c.to_dict())+"\n")
        tmp.replace(CONF_FILE)
    def find_by_ip(self, ip: str) -> CameraConf | None:
        for c in self.load_all():
            if c.ip==ip: return c
        return None
