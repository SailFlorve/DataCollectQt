from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout

from util.tools import UITool
from widget.base_widget import BaseWidget


class StatusBar(BaseWidget):
    def __init__(self):
        from statusbar.status_bar_controller import StatusBarController

        super(StatusBar, self).__init__()
        self.vBoxRoot = QVBoxLayout(self)
        self.hBoxWidget = QWidget()
        self.hBoxStatus = QHBoxLayout(self.hBoxWidget)
        self.labelCopyright = QLabel("copyright©2021 南京理工大学 v1.0")
        self.labelStatusIcon = QLabel()
        self.labelStatus = QLabel()

        self.controller = StatusBarController(self)

        self.__initView()

    def __getQss(self) -> [dict, None]:
        return {self: "QWidget {background-color:#ffffff}"
                      "QLabel {font-size: 16px;"
                      "color: #a8a8a8; }"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        self.labelCopyright.setAlignment(Qt.AlignCenter)
        self.labelStatus.setText("Running")

        self.hBoxStatus.setContentsMargins(20, 0, 20, 0)
        self.hBoxStatus.addWidget(self.labelStatusIcon, 1)
        self.hBoxStatus.addWidget(self.labelStatus, 10)
        self.hBoxStatus.addWidget(self.labelCopyright, 11)
        self.hBoxStatus.addStretch(11)

        self.vBoxRoot.setContentsMargins(0, 0, 0, 0)
        self.vBoxRoot.setSpacing(0)
        self.vBoxRoot.addWidget(UITool.getLineFrame(1, "#c5c5c5"))
        self.vBoxRoot.addWidget(self.hBoxWidget, 1)

        self.setLayout(self.vBoxRoot)

    def setRunningStatus(self, running: bool):
        icon = ":/ic_running.png" if running else ":/ic_not_running"
        UITool.setLabelStyle(self.labelStatusIcon, icon=icon, size=QSize(15, 15))

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.controller.monitorThread.terminate()
