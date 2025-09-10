import time
from typing import NamedTuple
from domain.models import FileEvent, Direction
from domain.heuristics import decide_direction
from .ports import CameraRepo, CountsRepo

class EventOutcome(NamedTuple):
    direction: Direction

class EventProcessor:
    def __init__(self, cams: CameraRepo, counts: CountsRepo):
        self.cams = cams; self.counts = counts

    def handle(self, ev: FileEvent) -> EventOutcome:
        cam = self.cams.find_by_ip(ev.camera_ip)
        direction = decide_direction(cam, ev.raw_name)
        row = {"ts": ev.when if ev.when else time.time(),
               "camera_ip": ev.camera_ip,
               "camera_name": (cam.name if cam and cam.name else ev.camera_ip),
               "direction": direction, "file": ev.path, "raw": ev.raw_name}
        self.counts.append(row)
        return EventOutcome(direction)
