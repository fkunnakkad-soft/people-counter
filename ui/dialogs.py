from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from domain.models import CameraConf


class CameraDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, cam: CameraConf | None = None):
        super().__init__(parent)
        self.setWindowTitle("Camera")
        self.setModal(True)

        # --- fields ---
        self.name = QtWidgets.QLineEdit()
        self.ip   = QtWidgets.QLineEdit()
        self.brand = QtWidgets.QComboBox(); self.brand.addItems(["Hikvision", "Dahua", "Generic"])
        self.login = QtWidgets.QLineEdit()
        self.pwd   = QtWidgets.QLineEdit(); self.pwd.setEchoMode(QtWidgets.QLineEdit.Password)
        self.dir   = QtWidgets.QComboBox(); self.dir.addItems(["A->B", "A<-B", "A<->B"])
        self.pattern = QtWidgets.QLineEdit()

        # Enabled should be clickable
        self.enabled = QtWidgets.QCheckBox("Enabled")
        self.enabled.setChecked(True)
        self.enabled.setEnabled(True)

        # NEW: Protocol combo (HTTP default, HTTPS available)
        self.proto = QtWidgets.QComboBox()
        self.proto.addItems(["HTTP", "HTTPS"])
        self.proto.setCurrentText("HTTP")  # default

        # --- form layout ---
        form = QtWidgets.QFormLayout()
        form.addRow("Name", self.name)
        form.addRow("IP", self.ip)
        form.addRow("Brand", self.brand)
        form.addRow("Username", self.login)
        form.addRow("Password", self.pwd)
        form.addRow("Protocol", self.proto)    # <— visible + working
        form.addRow("Direction", self.dir)
        form.addRow("Filename hint", self.pattern)
        form.addRow("", self.enabled)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(btns)

        # --- populate when editing ---
        if cam:
            self.name.setText(cam.name)
            self.ip.setText(cam.ip)
            self.brand.setCurrentText(cam.brand)
            self.login.setText(cam.login)
            self.pwd.setText(cam.password)
            self.dir.setCurrentText(cam.direction)
            self.pattern.setText(cam.pattern_hint)
            self.enabled.setChecked(cam.enabled)

            # accept both new and old models (old may not have 'scheme')
            current_scheme = getattr(cam, "scheme", "http")
            self.proto.setCurrentText((current_scheme or "http").upper())

    def to_conf(self) -> CameraConf:
        # Build the standard CameraConf first (compatible with your current model)
        conf = CameraConf(
            name=self.name.text().strip(),
            ip=self.ip.text().strip(),
            brand=self.brand.currentText(),
            login=self.login.text().strip(),
            password=self.pwd.text(),
            direction=self.dir.currentText(),
            pattern_hint=(self.pattern.text().strip() or "LINE_CROSSING_DETECTION"),
            enabled=self.enabled.isChecked(),
        )
        # NEW: stash the chosen scheme on the instance so the rest of the app can read it.
        # This is safe even if 'scheme' isn't in the dataclass yet; we'll formalize it next.
        try:
            setattr(conf, "scheme", self.proto.currentText().lower())  # "http" or "https"
        except Exception:
            pass
        return conf


class CsvDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export CSV")
        now = QtWidgets.QDateTime.currentDateTime()
        start = now.addDays(-1)

        self.dt_from = QtWidgets.QDateTimeEdit(start); self.dt_from.setCalendarPopup(True)
        self.dt_to   = QtWidgets.QDateTimeEdit(now);   self.dt_to.setCalendarPopup(True)

        form = QtWidgets.QFormLayout()
        form.addRow("From", self.dt_from)
        form.addRow("To",   self.dt_to)

        self.ok = QtWidgets.QPushButton("Export")
        self.cancel = QtWidgets.QPushButton("Cancel")
        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.ok)
        row.addWidget(self.cancel)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(form)
        lay.addLayout(row)
