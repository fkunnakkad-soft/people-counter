import re
from .models import Direction, CameraConf

def tokenize(raw: str) -> set[str]:
    return {t.upper() for t in re.split(r"[^A-Za-z0-9]+", raw) if t}

def guess_event_direction_from_tokens(tokens: set[str]) -> Direction:
    n_in  = ("IN", "ENTER", "ENTRANCE", "REGION_ENTRANCE", "INTRUSION", "LINE_CROSSING_IN")
    n_out = ("OUT", "EXIT", "LINE_CROSSING_OUT")
    if "LINE" in tokens and any(x in tokens for x in n_in): return "IN"
    if "LINE" in tokens and any(x in tokens for x in n_out): return "OUT"
    if "REGION_ENTRANCE" in tokens or "INTRUSION" in tokens: return "IN"
    return "?"

def decide_direction(cam: CameraConf | None, raw_name: str) -> Direction:
    tokens = tokenize(raw_name)
    if cam and cam.pattern_hint and cam.pattern_hint.upper() in tokens:
        if cam.direction == "A->B": return "IN"
        if cam.direction == "A<-B": return "OUT"
        g = guess_event_direction_from_tokens(tokens); return g if g != "?" else "IN"
    g = guess_event_direction_from_tokens(tokens)
    if g != "?": return g
    if cam: return "OUT" if cam.direction == "A<-B" else "IN"
    return "IN"
