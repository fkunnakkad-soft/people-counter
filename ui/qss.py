LIGHT_QSS = """
* { font-family: Inter, Segoe UI, Ubuntu, system-ui, -apple-system; font-size: 13px; }
QMainWindow, QWidget { background: #f7f8fb; color: #1f2430; }
QGroupBox { border: 1px solid #e2e6ef; border-radius: 10px; margin-top: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #3b4353; }
QMenuBar { background: #ffffff; border-bottom: 1px solid #e6e9f2; }
QStatusBar { background: #ffffff; border-top: 1px solid #e6e9f2; color: #3b4353; }
QPushButton { background: #4663ff; color: white; border: none; padding: 7px 12px; border-radius: 8px; }
QPushButton:hover { background: #5a74ff; }
QPushButton:disabled { background: #cfd6ee; color: #8a94a6; }
QLineEdit, QComboBox, QSpinBox, QDateTimeEdit, QTextEdit, QPlainTextEdit {
  background: #ffffff; color: #1f2430; border: 1px solid #dbe1ee; border-radius: 8px; padding: 6px 8px;
}
QTabWidget::pane { border: 1px solid #e2e6ef; border-radius: 10px; background: #ffffff; }
QTabBar::tab {
  background: #f0f3fa; color: #3b4353; padding: 8px 14px; border: 1px solid #e2e6ef; border-bottom: none;
  border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 4px;
}
QTabBar::tab:selected { background: #ffffff; color: #1f2430; border-color: #cfd6ee; }
QListWidget, QTreeWidget { background: #ffffff; border: 1px solid #e2e6ef; border-radius: 10px; }
QListWidget::item { padding: 8px; }
QListWidget::item:selected { background: #e8edff; color: #1f2430; }
"""
