import sys

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QLineEdit, QPushButton

from bean import constant
from util.tools import UITool
from widget.base_widget import BaseWidget
from widget.custom_msgbox import CustomMsgBox


class LoginWidget(BaseWidget):
    loginSignal = pyqtSignal(str, bool)

    def __init__(self):
        from login.login_controller import LoginController

        super(LoginWidget, self).__init__()
        self.controller = LoginController(self)

        self.vBoxLogin = QVBoxLayout(self)
        self.labelTitle = QLabel(constant.APP_NAME)
        self.labelUsername = QLabel("账户")
        self.labelPwd = QLabel("密码")
        self.editUsername = QLineEdit()
        self.editPwd = QLineEdit()
        self.btnLogin = QPushButton("登录")
        self.btnShowPwd: QPushButton = QPushButton(self.editPwd)

        self.widthEdit = 50
        self.marginLeftRight = 180
        self.widthBtnShowPwd = 40

        self.__initView()
        self.__initEvents()

    def __getQss(self) -> dict:
        return {self: "QWidget {background-color: #FFFFFF;} "
                      "QLabel {font-size: 20px;"
                      "color: #757576; }"
                      "QLineEdit {"
                      "border: 1px solid;"
                      "border-radius:5px;"
                      "border-color:#c8ccd4;"
                      "font-size:18px;"
                      "color: #737373;"
                      "}",
                self.labelTitle: "{font-size:25px;"
                                 "color:#757576; }",
                self.btnLogin: """
                       QPushButton {
                           background-color: rgb(33, 152, 248);
                           border-radius:5px;
                           color:#FFFFFF;
                           font-size:20px;
                           }
                           QPushButton:hover {
                           background-color: rgb(30, 122, 230);
                           border-radius:5px;
                           color:#FFFFFF;
                           font-size:20px;
                        }""",
                self.btnShowPwd: "border-image: url(:/ic_show_pwd.png); border: none}"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        self.labelTitle.setAlignment(Qt.AlignCenter)

        self.editUsername.setFixedHeight(self.widthEdit)
        self.editUsername.setPlaceholderText("请输入您的帐户")
        self.editUsername.setTextMargins(25, 0, 25, 0)

        self.editPwd.setFixedHeight(self.widthEdit)
        self.editPwd.setPlaceholderText("请输入您的密码")
        self.editPwd.setTextMargins(25, 0, 25, 0)
        self.editPwd.setEchoMode(QLineEdit.Password)

        self.btnShowPwd.resize(self.widthBtnShowPwd, self.widthBtnShowPwd)

        self.btnLogin.setFixedHeight(50)

        self.vBoxLogin.addWidget(self.labelTitle, 8)
        self.vBoxLogin.addWidget(self.labelUsername, 5)
        self.vBoxLogin.addWidget(self.editUsername, 5)
        self.vBoxLogin.addStretch(1)
        self.vBoxLogin.addWidget(self.labelPwd, 5)
        self.vBoxLogin.addWidget(self.editPwd, 5)
        self.vBoxLogin.addStretch(5)
        self.vBoxLogin.addWidget(self.btnLogin, 5)
        self.vBoxLogin.setSpacing(0)
        self.vBoxLogin.setContentsMargins(self.marginLeftRight, 40, self.marginLeftRight, 180)

        self.setLayout(self.vBoxLogin)

        self.editUsername.setText("admin")
        self.editPwd.setText("admin")

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        newX = a0.size().width() - self.marginLeftRight * 2 - self.widthBtnShowPwd - 25
        newY = int((self.widthEdit - self.widthBtnShowPwd) / 2)
        self.btnShowPwd.move(newX, newY)

    def __initEvents(self):
        self.btnShowPwd.setCursor(QCursor(Qt.PointingHandCursor))
        self.btnShowPwd.clicked.connect(self.__changePwdStatus)
        self.btnLogin.clicked.connect(lambda: self.controller.login(self.editUsername.text(), self.editPwd.text()))

    def __changePwdStatus(self):
        btnCss = "border-image: url(%s); border: none; "

        if self.editPwd.echoMode() == QLineEdit.Password:
            self.editPwd.setEchoMode(QLineEdit.Normal)
            UITool.setQss({self.btnShowPwd: btnCss % ":/ic_hide_pwd.png"})
        else:
            self.editPwd.setEchoMode(QLineEdit.Password)
            UITool.setQss({self.btnShowPwd: btnCss % ":/ic_show_pwd.png"})

    def onLoginFinish(self, success, msg):
        if not success:
            CustomMsgBox.showMsg("登录失败", CustomMsgBox.ICON_QUESTION)
        else:
            self.loginSignal.emit(self.editUsername.text(), True)

    def onLogout(self, name: str):
        self.editUsername.clear()
        self.editPwd.clear()
        self.editUsername.setFocus()
        self.loginSignal.emit(name, False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = LoginWidget()
    w.resize(900, 640)
    w.show()
    sys.exit(app.exec_())
