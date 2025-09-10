from dataclasses import dataclass
from typing import Literal

Direction = Literal["IN", "OUT", "?"]

@dataclass
class CameraConf:
    name: str = ""
    ip: str = ""
    brand: str = "Hikvision"
    login: str = "admin"
    password: str = ""
    direction: str = "A->B"
    pattern_hint: str = "LINE_CROSSING_DETECTION"
    enabled: bool = True
    use_https: bool = False
    snap_channel: int = 101

    def to_dict(self) -> dict:
        return {
            "name": self.name, "ip": self.ip, "brand": self.brand,
            "login": self.login, "password": self.password,
            "direction": self.direction, "pattern_hint": self.pattern_hint,
            "enabled": self.enabled, "use_https": self.use_https,
            "snap_channel": self.snap_channel,
        }

    @staticmethod
    def from_dict(d: dict) -> "CameraConf":
        return CameraConf(
            name=d.get("name", ""), ip=d.get("ip", ""), brand=d.get("brand", "Hikvision"),
            login=d.get("login", "admin"), password=d.get("password", ""),
            direction=d.get("direction", "A->B"),
            pattern_hint=d.get("pattern_hint", "LINE_CROSSING_DETECTION"),
            enabled=bool(d.get("enabled", True)),
            use_https=bool(d.get("use_https", False)),
            snap_channel=int(d.get("snap_channel", 101)),
        )

@dataclass
class FileEvent:
    path: str
    camera_ip: str
    raw_name: str
    when: float
