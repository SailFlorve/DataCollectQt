import time

from PyQt5.QtCore import QThread, QObject, pyqtSignal

from statusbar.status_bar_ui import StatusBar
from util.tools import WinTool


class StatusBarController(QObject):
    runningSignal = pyqtSignal(bool)

    def __init__(self, widget: StatusBar):
        super(StatusBarController, self).__init__()
        self.widget = widget
        self.processType = None
        self.processDict = {0: "WXWork.exe", 1: "WeChat.exe", 2: "QQ.exe"}

        self.runningSignal.connect(self.widget.setRunningStatus)

        self.monitorThread = QThread()
        self.monitorThread.run = self.__startMonitoring
        self.monitorThread.start()

    def __startMonitoring(self):
        while True:
            if self.processType is not None:
                running, _ = WinTool.isProcessExists(self.processDict[self.processType])
                self.runningSignal.emit(running)
            else:
                self.runningSignal.emit(False)

            time.sleep(1)
