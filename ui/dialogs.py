from PySide6 import QtWidgets
from domain.models import CameraConf

class CameraDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, cam: CameraConf | None = None):
        super().__init__(parent)
        self.setWindowTitle("Camera")
        self.setModal(True)

        self.name = QtWidgets.QLineEdit()
        self.ip = QtWidgets.QLineEdit()
        self.brand = QtWidgets.QComboBox(); self.brand.addItems(["Hikvision","Dahua","Generic"])
        self.login = QtWidgets.QLineEdit()
        self.pwd = QtWidgets.QLineEdit(); self.pwd.setEchoMode(QtWidgets.QLineEdit.Password)
        self.dir = QtWidgets.QComboBox(); self.dir.addItems(["A->B","A<-B","A<->B"])
        self.pattern = QtWidgets.QLineEdit()
        self.enabled = QtWidgets.QCheckBox("Enabled"); self.enabled.setChecked(True)
        self.https = QtWidgets.QCheckBox("Use HTTPS")
        self.snap = QtWidgets.QSpinBox(); self.snap.setRange(1,999); self.snap.setValue(101)

        form = QtWidgets.QFormLayout()
        form.addRow("Name", self.name); form.addRow("IP", self.ip)
        form.addRow("Brand", self.brand); form.addRow("Username", self.login)
        form.addRow("Password", self.pwd); form.addRow("Direction", self.dir)
        form.addRow("Filename hint", self.pattern); form.addRow("Snapshot channel", self.snap)
        form.addRow("", self.https); form.addRow("", self.enabled)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay = QtWidgets.QVBoxLayout(self); lay.addLayout(form); lay.addWidget(btns)

        if cam:
            self.name.setText(cam.name); self.ip.setText(cam.ip); self.brand.setCurrentText(cam.brand)
            self.login.setText(cam.login); self.pwd.setText(cam.password); self.dir.setCurrentText(cam.direction)
            self.pattern.setText(cam.pattern_hint); self.enabled.setChecked(cam.enabled)
            self.https.setChecked(cam.use_https); self.snap.setValue(cam.snap_channel)

    def to_conf(self) -> CameraConf:
        return CameraConf(
            name=self.name.text().strip(), ip=self.ip.text().strip(), brand=self.brand.currentText(),
            login=self.login.text().strip(), password=self.pwd.text(), direction=self.dir.currentText(),
            pattern_hint=self.pattern.text().strip() or "LINE_CROSSING_DETECTION",
            enabled=self.enabled.isChecked(), use_https=self.https.isChecked(),
            snap_channel=int(self.snap.value()),
        )

class CsvDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Export CSV")
        now = QtWidgets.QDateTime.currentDateTime(); start = now.addDays(-1)
        self.dt_from = QtWidgets.QDateTimeEdit(start); self.dt_from.setCalendarPopup(True)
        self.dt_to = QtWidgets.QDateTimeEdit(now); self.dt_to.setCalendarPopup(True)
        form = QtWidgets.QFormLayout(); form.addRow("From", self.dt_from); form.addRow("To", self.dt_to)
        ok = QtWidgets.QPushButton("Export"); cancel = QtWidgets.QPushButton("Cancel")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        row = QtWidgets.QHBoxLayout(); row.addStretch(1); row.addWidget(ok); row.addWidget(cancel)
        lay = QtWidgets.QVBoxLayout(self); lay.addLayout(form); lay.addLayout(row)
