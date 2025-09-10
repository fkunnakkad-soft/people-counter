import re, time, tempfile, threading, warnings
from typing import Callable, List
from PySide6 import QtCore
import requests
from requests.auth import HTTPDigestAuth

from domain.models import FileEvent, CameraConf
from application.ports import EventSource, ImageStore
from infrastructure.jsonl_camera_repo import JsonlCameraRepo

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

def _token_from_event_type(et: bytes | str) -> str:
    if isinstance(et, bytes):
        e = et.decode(errors="ignore").lower()
    else:
        e = str(et).lower()
    # Map many names down to 3 canonical tokens we use in the app
    if "line" in e and ("cross" in e or "detect" in e):
        return "LINE_CROSSING_DETECTION"
    if "regionentrance" in e or ("region" in e and "entrance" in e):
        return "REGION_ENTRANCE"
    if "intrusion" in e:
        return "INTRUSION"
    if "motion" in e or "vmd" in e:
        return "MOTION"
    return e.upper()

class _CamWorker(QtCore.QThread):
    def __init__(self, cam: CameraConf, image_store: ImageStore,
                 on_file: Callable[[FileEvent], None],
                 on_log: Callable[[str], None]):
        super().__init__()
        self.cam = cam
        self.image_store = image_store
        self.on_file = on_file
        self.on_log = on_log
        self._stop = threading.Event()

    def _url(self, path: str) -> tuple[str, bool]:
        # Use the new camera field if present; fall back to any legacy 'use_https'
        scheme = (getattr(self.cam, "scheme", None) or ("https" if getattr(self.cam, "use_https", False) else "http")).lower()
        verify = False if scheme == "https" else True   # accept self-signed certs on HTTPS
        return f"{scheme}://{self.cam.ip}{path}", verify


    def _auth(self):
        return HTTPDigestAuth(self.cam.login, self.cam.password)

    def _snapshot(self, ch: int | None = None) -> str | None:
        # prefer channel from event; fall back to camera's configured snapshot channel (101)
        chan = int(ch or getattr(self.cam, "snap_channel", 101))
        url, verify = self._url(f"/ISAPI/Streaming/channels/{chan}/picture?snapShotImageType=JPEG")
        try:
            r = requests.get(url, auth=self._auth(), timeout=(5, 10), verify=verify, stream=True)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                for b in r.iter_content(8192):
                    if not b:
                        break
                    tmp.write(b)
                return tmp.name
        except Exception as e:
            self.on_log(f"Snapshot error {self.cam.ip}: {e}")
            return None


    def run(self):
        # Ignore noisy/periodic event types and only act on 'active' (start) events
        NOISY = {
            "VIDEOLOSS", "MOTION", "VMD", "SCENECHANGEDETECTION",
            "DEFOCUSDETECTION", "AUDIOEXCEPTION", "SHELTERALARM",
            "ALARMINPUT", "HOSTALARM", "VIDEOMISMATCH"
        }
        EVENT_BLOCK = re.compile(
            br"<EventNotificationAlert.*?</EventNotificationAlert>",
            re.IGNORECASE | re.DOTALL
        )
        GET = lambda tag, blob: re.search(
            fr"<{tag}>([^<]+)</{tag}>".encode(),
            blob, re.IGNORECASE | re.DOTALL
        )

    while not self._stop.is_set():
        try:
            url, verify = self._url("/ISAPI/Event/notification/alertStream")
            with requests.get(url, auth=self._auth(), stream=True, timeout=(5, 60), verify=verify) as r:
                r.raise_for_status()
                self.on_log(f"ISAPI connected: {self.cam.ip} ({'HTTPS' if verify is False else 'HTTP'})")
    
                buf = b""
                last = 0.0
                for chunk in r.iter_content(chunk_size=4096):
                    if self._stop.is_set():
                        break
                    if not chunk:
                        continue
                    buf += chunk
    
                    keep_from = 0
                    for m in EVENT_BLOCK.finditer(buf):
                        part = m.group(0)
    
                        m_type  = GET("eventType", part)
                        m_state = GET("eventState", part)
                        m_ch    = GET("channelID", part)
    
                        if not m_type:
                            continue
    
                        et = m_type.group(1).strip().decode(errors="ignore").lower()
                        state = (m_state.group(1).strip().decode(errors="ignore").lower()
                                 if m_state else "active")
                        ch = int(m_ch.group(1)) if m_ch else getattr(self.cam, "snap_channel", 101)
    
                        # Always log the raw event
                        self.on_log(f"Event {self.cam.ip}: eventType={et}, state={state}")
    
                        token = _token_from_event_type(et)
    
                        # Skip noisy types and 'inactive' (stop) events
                        if token in NOISY or state != "active":
                            keep_from = m.end()
                            continue
    
                        now = time.time()
                        if now - last < 0.5:  # debounce per cam
                            keep_from = m.end()
                            continue
                        last = now
    
                        tmp = self._snapshot(ch)
                        if not tmp:
                            # count even if snapshot fails
                            self.on_file(FileEvent(path="", camera_ip=self.cam.ip,
                                                   raw_name=token, when=now))
                        else:
                            dest = self.image_store.move_and_stamp(tmp, self.cam.ip, f"{token}.jpg")
                            self.on_file(FileEvent(path=dest, camera_ip=self.cam.ip,
                                                   raw_name=f"{token}.jpg", when=now))
    
                        keep_from = m.end()
    
                    if keep_from:
                        buf = buf[keep_from:]
    
        except requests.RequestException as e:
            self.on_log(f"ISAPI stream error {self.cam.ip}: {e}; retrying in 3s")
            # Helpful hint when HTTPS was selected but camera refuses 443
            _, v = self._url("/")  # v == False means HTTPS
            if v is False:
                self.on_log("Hint: HTTPS may be disabled on the camera. Enable it or switch Protocol to HTTP in the camera settings.")
            time.sleep(3)
        except Exception as e:
            self.on_log(f"ISAPI worker error {self.cam.ip}: {e}; retrying in 3s")
            time.sleep(3)

                

    def stop(self):
        self._stop.set()

class IsapiEventSource(EventSource):
    """Starts one worker per enabled camera from the JSONL repo."""
    def __init__(self, image_store: ImageStore, cam_repo: JsonlCameraRepo):
        self._image_store = image_store
        self._repo = cam_repo
        self._workers: List[_CamWorker] = []

    def start(self, on_file: Callable[[FileEvent], None], on_log: Callable[[str], None]) -> None:
        if any(w.isRunning() for w in self._workers):
            on_log("ISAPI already running")
            return
        self._workers = []
        for cam in self._repo.load_all():
            if not getattr(cam, "enabled", True):
                continue
            w = _CamWorker(cam, self._image_store, on_file, on_log)
            self._workers.append(w)
            w.start()
        on_log(f"ISAPI started for {len(self._workers)} cameras")

    def stop(self) -> None:
        for w in self._workers:
            try:
                w.stop()
                w.wait(1500)
            except Exception:
                pass
        self._workers = []

    def is_running(self) -> bool:
        return any(w.isRunning() for w in self._workers)
