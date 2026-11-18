# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from pathlib import Path
from .dialog import AccessibilityDialog


class AccessibilityPrototypePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        self.action = QAction("G-CHAM Network Analysis", self.iface.mainWindow())
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.action.setIcon(QIcon(str(icon_path)))
        self.action.triggered.connect(self.run)
        # addPluginToMenu()は指定名のサブメニューを作るため、
        # pluginMenu()へ直接追加してプラグインメニュー直下に表示する。
        self.iface.pluginMenu().addAction(self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.pluginMenu().removeAction(self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

    def run(self):
        try:
            self.dialog = AccessibilityDialog(self.iface)
            self.dialog.show()
            self.dialog.exec()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), "G-CHAM Network Analysis", str(exc))
