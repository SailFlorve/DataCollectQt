import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QVBoxLayout, QApplication, QFrame, QStackedWidget, QSizePolicy, QMainWindow, QPushButton, \
    QMessageBox

from account.account_ui import AccountWidget
from bean import constant
from login.login_ui import LoginWidget
from settings.settings_ui import SettingsWidget
from statusbar.status_bar_ui import StatusBar
from titlebar.title_bar_ui import TitleBar
from util.tools import UITool
from widget.base_widget import BaseWidget
from widget.layout_widget import VBoxLayoutWidget


class MainWindow(QMainWindow, BaseWidget):
    STATUS_LOGIN = 0
    STATUS_ACCOUNT = 1
    STATUS_SETTINGS = 2

    def __init__(self):
        super(MainWindow, self).__init__()

        self.rootView = QFrame(self)
        self.vBoxLayout = QVBoxLayout(self.rootView)

        self.titleBar = TitleBar(self)
        self.contentView = QStackedWidget()
        self.statusBar = StatusBar()

        self.loginWidget = LoginWidget()
        self.accountWidget = AccountWidget()
        self.settingsWidget = SettingsWidget()

        self.btnLogout = QPushButton("退出")

        self.widgetLogout = VBoxLayoutWidget(self)

        self.__initView()

        self.setCentralWidget(self.rootView)

    def __getQss(self) -> [dict, None]:
        return {self: "QMainWindow {border: 1px solid #EEEEEE }"
                      "QAbstractButton {outline: none}",
                self.btnLogout: "padding:10px; color:white; font-size: 15px; border:none; border-radius: 8px;"
                                "background-color: black",
                self.widgetLogout: "background-color: green"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setFixedSize(900, 700)
        self.setContentsMargins(1, 1, 1, 1)
        self.setWindowTitle(constant.APP_NAME)
        self.setWindowIcon(QIcon(":/ic_logo.png"))

        UITool.setCursor(Qt.PointingHandCursor, self.btnLogout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        self.titleBar.setFixedHeight(60)
        self.statusBar.setFixedHeight(50)

        self.btnLogout.setFixedSize(90, 40)
        self.widgetLogout.setFixedSize(90, self.btnLogout.height() + self.titleBar.btnUser.height() + 10)
        self.widgetLogout.setVisible(False)
        self.widgetLogout.layout.addStretch(1)
        self.widgetLogout.layout.addWidget(self.btnLogout)

        self.contentView.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.contentView.addWidget(self.loginWidget)
        self.contentView.addWidget(self.accountWidget)
        self.contentView.addWidget(self.settingsWidget)

        self.vBoxLayout.addWidget(self.titleBar, 1)
        self.vBoxLayout.addWidget(self.contentView, 1)
        self.vBoxLayout.addWidget(self.statusBar)

        self.loginWidget.loginSignal.connect(
            lambda username, login: self.__changeStatus(self.STATUS_ACCOUNT if login else self.STATUS_LOGIN, username))

        self.titleBar.settingsClickedSignal.connect(
            lambda isChecked: self.__changeStatus(
                self.STATUS_SETTINGS if isChecked else self.STATUS_ACCOUNT, isChecked))

        self.accountWidget.appChangeSignal.connect(self.__changeProcessType)

        self.settingsWidget.btnClose.clicked.connect(lambda: self.titleBar.btnSettings.click())
        self.btnLogout.clicked.connect(self.__logout)

        self.titleBar.btnUser.enterEvent = self.__onLogoutMenuEnterEvent
        self.widgetLogout.leaveEvent = self.__onLogoutMenuLeaveEvent

        self.__changeStatus(self.STATUS_LOGIN)

    def __logout(self):
        self.widgetLogout.setVisible(False)
        self.loginWidget.controller.logout()

    def __changeStatus(self, status: int, *args):
        self.contentView.setCurrentIndex(status)

        titleBarBtnShow = True if status != self.STATUS_LOGIN else False
        self.titleBar.btnSettings.setVisible(titleBarBtnShow)
        self.titleBar.btnUser.setVisible(titleBarBtnShow)
        self.titleBar.labelTitle.setVisible(titleBarBtnShow)

        if status == self.STATUS_LOGIN:
            self.__changeProcessType(None)
        elif status == self.STATUS_ACCOUNT:
            if type(args[0]) is str:  # 登录进来
                self.accountWidget.onToolBtnClicked(0)
                self.titleBar.btnUser.setText(args[0])
        elif status == self.STATUS_SETTINGS:
            self.__changeProcessType(None)

    def __changeProcessType(self, t):
        # 修改statusbar controller中的进程类型，用于检测不同的进程
        self.statusBar.controller.processType = t

    def __onLogoutMenuEnterEvent(self, a0: QtCore.QEvent):
        btnUserPos = UITool.getWidgetPos(self.titleBar.btnUser, self)

        self.widgetLogout.move(btnUserPos.x(), btnUserPos.y())
        self.widgetLogout.setVisible(True)

    def __onLogoutMenuLeaveEvent(self, a0: QtCore.QEvent):
        self.widgetLogout.setVisible(False)


if __name__ == '__main__':
    def catch_exceptions(ty, value, traceback):
        """
            捕获异常，并弹窗显示
        :param ty: 异常的类型
        :param value: 异常的对象
        :param traceback: 异常的traceback
        """

        print(ty, value, traceback)
        QMessageBox.critical(mw, "程序异常", str((ty, value)))
        oldHook(ty, value, traceback)


    oldHook = sys.excepthook
    sys.excepthook = catch_exceptions

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei"))

    mw = MainWindow()
    mw.show()

    execRes = app.exec_()
    sys.exit(execRes)
