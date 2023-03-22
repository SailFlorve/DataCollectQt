import sys
import time

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt5.QtWidgets import QLabel, QPushButton, QApplication, QGridLayout

from util.tools import UITool
from widget.base_widget import BaseWidget

box: "CustomMsgBox" = None


class CustomMsgBox(BaseWidget):
    okSignal = pyqtSignal()
    cancelSignal = pyqtSignal()

    closeSignal = pyqtSignal()

    ICON_OK = 0
    ICON_QUESTION = 1
    TYPE_DIALOG = 0
    TYPE_TOAST = 1
    TYPE_STATUS = 2

    def __init__(self, typ, showOkBtn: bool = True, showCancelBtn: bool = True):
        super(CustomMsgBox, self).__init__()
        self.setObjectName("layout")
        self.gridRoot = QGridLayout(self)

        self.labelIcon = QLabel()
        self.labelText = QLabel()
        self.btnCancel = QPushButton("取消")
        self.btnOk = QPushButton("确认")
        self.showOkBtn = showOkBtn
        self.showCancelBtn = showCancelBtn

        self.__initView()

        self.type = typ

        UITool.enableDragMove(self)

    def __getQss(self) -> [dict, None]:
        return {self: "QWidget#layout {background-color:white; border:1px solid rgb(0,0,0,20);border-radius:0px;}",
                self.labelText: "font-size:16px;",
                self.btnCancel: "color:#a2a2a2; background-color:#dbdbdb;border:none;border-radius:2px;font-size:14px",
                self.btnOk: "color:white; background-color:#168df1;border:none;border-radius:2px;font-size:14px"}

    def __initView(self):
        self.setWindowFlags(Qt.FramelessWindowHint)

        UITool.setQss(self.__getQss())

        self.btnOk.setFixedSize(45, 25)
        self.btnCancel.setFixedSize(45, 25)
        self.labelText.adjustSize()

        self.gridRoot.setSpacing(20)

        self.gridRoot.addWidget(self.labelIcon, 0, 0, 1, 1, alignment=Qt.AlignCenter)
        self.gridRoot.addWidget(self.labelText, 0, 1, 1, 3, alignment=Qt.AlignCenter | Qt.AlignLeft)

        if self.showOkBtn:
            self.gridRoot.addWidget(self.btnOk, 1, 3)

        if self.showCancelBtn:
            self.gridRoot.addWidget(self.btnCancel, 1, 2)

        self.gridRoot.setColumnStretch(1, 1)

        self.btnOk.clicked.connect(lambda: self.__onBtnClick(True))
        self.btnCancel.clicked.connect(lambda: self.__onBtnClick(False))

        self.closeSignal.connect(self.close)

    def __onBtnClick(self, isOk: bool):
        if isOk:
            self.okSignal.emit()
        else:
            self.cancelSignal.emit()
        self.close()

    def __delayClose(self, duration: float):
        time.sleep(duration)
        self.closeSignal.emit()

    @staticmethod
    def __createMsgBox(tp, text, iconType, showOkBtn=True, showCancelBtn=True):

        global box
        if box is not None:
            box.close()

        box = CustomMsgBox(tp, showOkBtn, showCancelBtn)

        print(box.width(), box.height())
        box.move(QApplication.desktop().screenGeometry().width() // 2 - 200,
                 QApplication.desktop().screenGeometry().height() // 2 - 100)

        box.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        box.setWindowFlags(Qt.ToolTip)
        box.setWindowTitle("提示")
        box.labelText.setText(text)
        UITool.setLabelStyle(box.labelIcon,
                             icon=":/ic_ok.png" if iconType == CustomMsgBox.ICON_OK else ":/ic_question.png",
                             size=QSize(18, 18))
        return box

    @staticmethod
    def showMsg(text, iconType=ICON_OK, okSlot=None, cancelSlot=None):
        msgBox = CustomMsgBox.__createMsgBox(0, text, iconType, showCancelBtn=cancelSlot is not None)
        if okSlot is not None:
            msgBox.okSignal.connect(okSlot)

        if cancelSlot is not None:
            msgBox.cancelSignal.connect(cancelSlot)

        msgBox.setWindowModality(Qt.ApplicationModal)
        msgBox.show()

    @staticmethod
    def showToast(text, iconType=0, duration=1.5):
        msgBox = CustomMsgBox.__createMsgBox(1, text, iconType, False, False)
        msgBox.btnOk.setVisible(False)
        msgBox.btnCancel.setVisible(False)
        msgBox.show()
        thread = QThread(msgBox)
        thread.run = lambda: msgBox.__delayClose(duration)
        thread.start()

    @staticmethod
    def showStatus(text):
        global box
        if box is not None and box.type == 2:
            box.labelText.setText(text)
            return

        msgBox = CustomMsgBox.__createMsgBox(2, text, 0, False, False)
        msgBox.setWindowModality(Qt.ApplicationModal)
        msgBox.btnOk.setVisible(False)
        msgBox.btnCancel.setVisible(False)
        msgBox.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    CustomMsgBox.showToast("123123")
    sys.exit(app.exec_())
