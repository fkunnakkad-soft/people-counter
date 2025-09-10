# domain/models.py
from dataclasses import dataclass
from typing import Literal, Iterable

Direction = Literal["IN", "OUT", "?"]
Scheme = Literal["http", "https"]


@dataclass
class CameraConf:
    name: str = ""
    ip: str = ""
    brand: str = "Hikvision"
    login: str = "admin"
    password: str = ""
    direction: str = "A->B"              # "A->B", "A<-B", "A<->B"
    pattern_hint: str = "LINE_CROSSING_DETECTION"
    enabled: bool = True
    scheme: Scheme = "http"              # NEW: "http" (default) or "https"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ip": self.ip,
            "brand": self.brand,
            "login": self.login,
            "password": self.password,
            "direction": self.direction,
            "pattern_hint": self.pattern_hint,
            "enabled": self.enabled,
            "scheme": self.scheme,       # NEW
        }

    @staticmethod
    def from_dict(d: dict) -> "CameraConf":
        return CameraConf(
            name=d.get("name", ""),
            ip=d.get("ip", ""),
            brand=d.get("brand", "Hikvision"),
            login=d.get("login", "admin"),
            password=d.get("password", ""),
            direction=d.get("direction", "A->B"),
            pattern_hint=d.get("pattern_hint", "LINE_CROSSING_DETECTION"),
            enabled=bool(d.get("enabled", True)),
            scheme=d.get("scheme", "http"),   # default to HTTP for old configs
        )


@dataclass
class FileEvent:
    path: str
    camera_ip: str
    raw_name: str
    when: float


@dataclass
class FtpConfig:
    addr: str
    port: int
    user: str
    password: str
    pasv_low: int
    pasv_high: int
    debounce_s: float = 1.0
