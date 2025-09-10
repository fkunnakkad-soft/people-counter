#!/usr/bin/env python3
import sys, os, csv
from PySide6 import QtCore, QtWidgets, QtGui
from shared.paths import ensure_dirs, KEEP_MIN, fmt_ts
from domain.models import CameraConf, FileEvent
from application.event_processor import EventProcessor
from infrastructure.jsonl_camera_repo import JsonlCameraRepo
from infrastructure.jsonl_counts_repo import JsonlCountsRepo
from infrastructure.image_store import LocalImageStore
from infrastructure.isapi_event_source import IsapiEventSource
from ui.qss import LIGHT_QSS
from ui.dialogs import CameraDialog, CsvDialog

class MainWin(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("People Counter (ISAPI)"); self.resize(1200, 750)
        ensure_dirs()
        self.camera_repo=JsonlCameraRepo(); self.counts_repo=JsonlCountsRepo()
        self.processor=EventProcessor(self.camera_repo, self.counts_repo)
        self.image_store=LocalImageStore(); self.event_source=IsapiEventSource(self.image_store, self.camera_repo)

        from collections import defaultdict, deque
        self.cameras: list[CameraConf] = self.camera_repo.load_all()
        self._counts = defaultdict(lambda: dict(IN=0, OUT=0, TOTAL=0))
        self._recent_by_camip = defaultdict(lambda: deque(maxlen=20))
        self._patterns_seen = set()

        tabs = QtWidgets.QTabWidget(); self.setCentralWidget(tabs)

        dash = QtWidgets.QWidget(); dash_lay = QtWidgets.QGridLayout(dash)
        self.total_in=QtWidgets.QLabel("0"); self.total_out=QtWidgets.QLabel("0"); self.total_all=QtWidgets.QLabel("0")
        for w in [self.total_in, self.total_out, self.total_all]: w.setAlignment(QtCore.Qt.AlignCenter); w.setStyleSheet("font-size:26px; font-weight:600;")
        box_sum=QtWidgets.QGroupBox("Totals"); g=QtWidgets.QGridLayout(box_sum)
        g.addWidget(QtWidgets.QLabel("IN"),0,0); g.addWidget(self.total_in,0,1)
        g.addWidget(QtWidgets.QLabel("OUT"),1,0); g.addWidget(self.total_out,1,1)
        g.addWidget(QtWidgets.QLabel("ALL"),2,0); g.addWidget(self.total_all,2,1)

        self.preview_label=QtWidgets.QLabel("Recent photo will appear here"); self.preview_label.setFixedHeight(280)
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter); self.preview_label.setStyleSheet("border:1px solid #e2e6ef; border-radius:10px;")
        box_prev=QtWidgets.QGroupBox("Most recent image"); v=QtWidgets.QVBoxLayout(box_prev); v.addWidget(self.preview_label)

        self.table=QtWidgets.QTableWidget(0,8); self.table.setHorizontalHeaderLabels(["Name","IP","Hint","HTTPS","Snap","A→B","A←B","Total"])
        self.table.horizontalHeader().setStretchLastSection(True); self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        box_tbl=QtWidgets.QGroupBox("Cameras"); tv=QtWidgets.QVBoxLayout(box_tbl); tv.addWidget(self.table)

        dash_lay.addWidget(box_sum,0,0,1,1); dash_lay.addWidget(box_prev,0,1,1,2); dash_lay.addWidget(box_tbl,1,0,1,3)

        cams=QtWidgets.QWidget(); cl=QtWidgets.QVBoxLayout(cams)
        self.cam_list=QtWidgets.QListWidget(); self.cam_list.setAlternatingRowColors(True)
        btn_row=QtWidgets.QHBoxLayout(); b_add=QtWidgets.QPushButton("＋ Add"); b_edit=QtWidgets.QPushButton("✎ Edit"); b_del=QtWidgets.QPushButton("🗑 Remove")
        btn_row.addWidget(b_add); btn_row.addWidget(b_edit); btn_row.addWidget(b_del); btn_row.addStretch(1)
        ctl=QtWidgets.QHBoxLayout(); self.b_start=QtWidgets.QPushButton("Start monitoring (ISAPI)"); self.b_stop=QtWidgets.QPushButton("Stop")
        self.b_test=QtWidgets.QPushButton("Test cameras"); self.b_export=QtWidgets.QPushButton("Export CSV")
        ctl.addWidget(self.b_start); ctl.addWidget(self.b_stop); ctl.addWidget(self.b_test); ctl.addStretch(1); ctl.addWidget(self.b_export)
        self.gallery=QtWidgets.QListWidget(); self.gallery.setViewMode(QtWidgets.QListView.IconMode)
        self.gallery.setIconSize(QtCore.QSize(160,90)); self.gallery.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.gallery.setMovement(QtWidgets.QListView.Static); self.gallery.setSpacing(8)
        gal_box=QtWidgets.QGroupBox("Recent photos (auto-purged)"); gl=QtWidgets.QVBoxLayout(gal_box); gl.addWidget(self.gallery)
        cl.addWidget(self.cam_list); cl.addLayout(btn_row); cl.addLayout(ctl); cl.addWidget(gal_box)

        tests=QtWidgets.QWidget(); tl=QtWidgets.QVBoxLayout(tests)
        self.patterns_edit=QtWidgets.QPlainTextEdit(); self.patterns_edit.setReadOnly(True)
        tl.addWidget(QtWidgets.QLabel("Filename tokens seen:")); tl.addWidget(self.patterns_edit)

        logs=QtWidgets.QWidget(); ll=QtWidgets.QVBoxLayout(logs)
        self.log_view=QtWidgets.QPlainTextEdit(); self.log_view.setReadOnly(True); self.log_view.setMaximumBlockCount(3000)
        ll.addWidget(self.log_view)

        tabs.addTab(dash,"Dashboard"); tabs.addTab(cams,"Cameras & Settings"); tabs.addTab(tests,"Detections Info"); tabs.addTab(logs,"Logs")
        mb=self.menuBar(); filem=mb.addMenu("&File"); a_save=filem.addAction("Save Config"); a_save.triggered.connect(self.save_config)
        a_load=filem.addAction("Load Config"); a_load.triggered.connect(self.load_config); filem.addSeparator()
        a_quit=filem.addAction("Quit"); a_quit.triggered.connect(self.close)
        b_add.clicked.connect(self.on_add); b_edit.clicked.connect(self.on_edit); b_del.clicked.connect(self.on_del)
        self.b_start.clicked.connect(self.on_start); self.b_stop.clicked.connect(self.on_stop)
        self.b_test.clicked.connect(self.on_self_test); self.b_export.clicked.connect(self.on_export)
        self.ui_timer=QtCore.QTimer(self); self.ui_timer.timeout.connect(self.refresh_counts); self.ui_timer.start(1500)
        self.gc_timer=QtCore.QTimer(self); self.gc_timer.timeout.connect(self.purge_old_images); self.gc_timer.start(20000)
        from ui.qss import LIGHT_QSS as _Q; self.setStyleSheet(_Q)
        self.refresh_cam_list(); self.refresh_table()

    def _on_log(self, msg:str): self.log_view.appendPlainText(msg)

    def _on_file(self, ev: FileEvent):
        import re
        toks=[t for t in re.split(r"[^A-Za-z0-9]+", ev.raw_name) if t]; up=set([t.upper() for t in toks])
        newly=sorted(list(up - self._patterns_seen))
        if newly: self._patterns_seen |= up; self.patterns_edit.appendPlainText(", ".join(newly))
        out=self.processor.handle(ev); direction=out.direction
        rec=self._counts[ev.camera_ip]
        if direction=="IN": rec["IN"]=rec.get("IN",0)+1
        elif direction=="OUT": rec["OUT"]=rec.get("OUT",0)+1
        rec["TOTAL"]=rec.get("IN",0)+rec.get("OUT",0)
        self._recent_by_camip[ev.camera_ip].append((ev.path, ev.when))
        self.show_latest_preview(); self.refresh_table()
        item=QtWidgets.QListWidgetItem(); base=os.path.basename(ev.path) if ev.path else ev.raw_name
        short=base[:28]+("…" if len(base)>28 else ""); item.setText(short)
        if ev.path and os.path.exists(ev.path):
            pm=QtGui.QPixmap(ev.path)
            if not pm.isNull():
                item.setIcon(QtGui.QIcon(pm.scaled(160,90, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)))
        self.gallery.insertItem(0, item)

    def on_add(self):
        d=CameraDialog(self)
        if d.exec()==QtWidgets.QDialog.Accepted:
            self.cameras.append(d.to_conf()); self.save_config(); self.refresh_cam_list(); self.refresh_table()

    def on_edit(self):
        row=self.cam_list.currentRow()
        if row<0: return
        d=CameraDialog(self, self.cameras[row])
        if d.exec()==QtWidgets.QDialog.Accepted:
            self.cameras[row]=d.to_conf(); self.save_config(); self.refresh_cam_list(); self.refresh_table()

    def on_del(self):
        row=self.cam_list.currentRow()
        if row<0: return
        cam=self.cameras[row]
        if QtWidgets.QMessageBox.question(self,"Remove", f"Remove camera “{cam.name or cam.ip}”?")==QtWidgets.QMessageBox.Yes:
            self.cameras.pop(row); self.save_config(); self.refresh_cam_list(); self.refresh_table()

    def on_start(self):
        self.event_source.start(self._on_file, self._on_log); self.statusBar().showMessage("Monitoring (ISAPI) started", 3000)

    def on_stop(self):
        self.event_source.stop(); self.statusBar().showMessage("Stopped", 3000)

    def on_self_test(self):
        import requests
        from requests.auth import HTTPDigestAuth
        ok,bad=[],[]
        for cam in self.cameras:
            if not cam.enabled: continue
            scheme="https" if cam.use_https else "http"; url=f"{scheme}://{cam.ip}/ISAPI/Event/notification/alertStream"
            try:
                r=requests.get(url, auth=HTTPDigestAuth(cam.login, cam.password), stream=True, timeout=3, verify=False)
                if r.status_code in (200,401,403): ok.append(cam.ip if r.ok else f"{cam.ip} (auth?)")
                else: bad.append(f"{cam.ip} (HTTP {r.status_code})")
            except Exception as e:
                bad.append(f"{cam.ip} ({e})")
        QtWidgets.QMessageBox.information(self,"Test", f"Reachable: {', '.join(ok) or '—'}\nIssues: {', '.join(bad) or '—'}")

    def on_export(self):
        dlg=CsvDialog(self)
        if dlg.exec()!=QtWidgets.QDialog.Accepted: return
        t0=dlg.dt_from.dateTime().toSecsSinceEpoch(); t1=dlg.dt_to.dateTime().toSecsSinceEpoch()
        rows=[]
        for ev in self.counts_repo.read_range(t0,t1):
            rows.append([fmt_ts(float(ev.get('ts',0))), ev.get('camera_name') or ev.get('camera_ip',''),
                         ev.get('camera_ip',''), ev.get('direction',''),
                         os.path.basename(ev.get('file','')) if ev.get('file') else '', ev.get('raw','')])
        if not rows: QtWidgets.QMessageBox.information(self,"Export","No rows in that time range."); return
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,"Save CSV","export.csv","CSV (*.csv)")
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["DateTime","Camera Name","Camera IP","Direction","Saved File","Original Name"]); w.writerows(rows)
        QtWidgets.QMessageBox.information(self,"Export", f"Saved: {path}")

    def save_config(self):
        self.camera_repo.save_all(self.cameras); self.statusBar().showMessage("Config saved", 2500)
    def load_config(self):
        self.cameras = self.camera_repo.load_all()
    def refresh_cam_list(self):
        self.cam_list.clear()
        for c in self.cameras:
            t=c.name or c.ip; sub=f"{c.brand}  •  {c.ip}  •  {'HTTPS' if c.use_https else 'HTTP'}  •  ch={c.snap_channel}  •  {c.direction}"
            self.cam_list.addItem(QtWidgets.QListWidgetItem(f"{t}\n{sub}"))
    def refresh_table(self):
        self.table.setRowCount(len(self.cameras)); tin=tout=tall=0
        for r,c in enumerate(self.cameras):
            rec=self._counts.get(c.ip,{"IN":0,"OUT":0,"TOTAL":0}); tin+=rec["IN"]; tout+=rec["OUT"]; tall+=rec["TOTAL"]
            vals=[c.name or c.ip, c.ip, c.pattern_hint, "✓" if c.use_https else "", str(c.snap_channel),
                  str(rec["IN"]), str(rec["OUT"]), str(rec["TOTAL"])]
            for col,v in enumerate(vals): self.table.setItem(r,col,QtWidgets.QTableWidgetItem(v))
        self.total_in.setText(str(tin)); self.total_out.setText(str(tout)); self.total_all.setText(str(tall))
    def show_latest_preview(self):
        latest_path=None; latest_ts=-1
        for q in self._recent_by_camip.values():
            if q and len(q):
                p,t=q[-1]
                if t>latest_ts: latest_ts=t; latest_path=p
        if latest_path and os.path.exists(latest_path):
            pm=QtGui.QPixmap(latest_path).scaled(self.preview_label.width(), self.preview_label.height(),
                                                 QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.preview_label.setPixmap(pm)
        else: self.preview_label.setText("Recent photo will appear here")
    def purge_old_images(self):
        n=self.image_store.purge_older_than(KEEP_MIN*60)
        if n: self._on_log(f"{n} old images purged")
    def refresh_counts(self):
        self.refresh_table(); self.show_latest_preview()
    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        try: self.on_stop()
        finally: return super().closeEvent(e)

def main():
    ensure_dirs(); app=QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    w=MainWin(); w.show(); sys.exit(app.exec())

if __name__ == "__main__": main()
