import sys
from abc import abstractmethod
from typing import List

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QListWidget, QApplication, QGridLayout, \
    QLabel, QPushButton, QToolButton, QHBoxLayout, QToolTip

from bean.beans import Account
from util import log
from util.tools import UITool
from widget.base_widget import BaseWidget
from widget.circle_image import CircleImage
from widget.custom_msgbox import CustomMsgBox
from widget.layout_widget import HBoxLayoutWidget


class AccountWidget(BaseWidget):
    APP_LOGO_SIZE = 20
    appChangeSignal = pyqtSignal(int)
    addAccountSignal = pyqtSignal(int)
    enableAddAccountSignal = pyqtSignal()
    showMsgSignal = pyqtSignal(int, str)

    def __init__(self):
        from account.account_controller import AccountController

        super(AccountWidget, self).__init__()
        self.controller = AccountController(self)

        self.gridRoot: QGridLayout = UITool.getLayout(QGridLayout(), self)

        self.labelTitle = QLabel("账号列表")
        self.btnRefresh = QPushButton()
        self.widgetLine = UITool.getLineFrame(1, "#d6d6d8")
        self.toolBtnWeCom = QToolButton()
        self.toolBtnWechat = QToolButton()
        self.toolBtnQQ = QToolButton()
        self.listUser = QListWidget()
        self.labelPage = QLabel("共1页")
        self.btnPrePage = QPushButton("<")
        self.labelCurrentPage = QLabel(" 1 ")
        self.btnNextPage = QPushButton(">")
        self.btnAddAccount = QPushButton("添加解密账号")

        self.toolBtnList = [self.toolBtnWeCom, self.toolBtnWechat, self.toolBtnQQ]

        self.__initView()

    def __getQss(self) -> [dict, None]:
        btnLabelStyle = "border: 1px solid #b6b6b7; color:#737373; font-size:16px;"

        return {self: "QWidget {background-color:#f4f4f6}"
                      "QToolButton {font-size:15px; border: none;  text-align: center; color:#494949} "
                      "QToolButton:checked {font-size:15px; border:0px; "
                      "border-bottom:2px solid #007bff; color:#007bff}",
                self.labelTitle: "color: rgb(0, 0, 0);font-size:20px",
                self.btnRefresh: "border:none; border-image: url(:/ic_refresh.png);",
                self.btnPrePage: btnLabelStyle,
                self.labelCurrentPage: btnLabelStyle,
                self.btnNextPage: btnLabelStyle,
                self.labelPage: "color:#737373; font-size:16px;",
                self.listUser: "QListWidget {background-color:transparent; border:none;}",
                self.btnAddAccount: "QPushButton {font-size:16px; border: none;  text-align: center; "
                                    "color:#FFFFFF; background-color:#2496ed;border-radius:5px } "
                                    "QPushButton:disabled {font-size:16px; border: none;  text-align: center; "
                                    "color:#FFFFFF; background-color:#d3d3d3;border-radius:5px } "}

    # noinspection PyUnresolvedReferences
    def __initView(self):
        UITool.setQss(self.__getQss())
        UITool.setCursor(Qt.PointingHandCursor, self.btnRefresh,
                         self.toolBtnWeCom, self.toolBtnWechat, self.toolBtnQQ,
                         self.btnPrePage, self.btnNextPage,
                         self.btnAddAccount)

        UITool.setButtonStyle(self.btnRefresh, size=QSize(20, 20))
        UITool.setButtonStyle(self.toolBtnWeCom, text="企业微信",
                              icon=UITool.getQIcon(":/ic_buswechat.png", self.APP_LOGO_SIZE, self.APP_LOGO_SIZE))
        UITool.setButtonStyle(self.toolBtnWechat, text="微信",
                              icon=UITool.getQIcon(":/ic_wechat.png", self.APP_LOGO_SIZE, self.APP_LOGO_SIZE))
        UITool.setButtonStyle(self.toolBtnQQ, text="QQ",
                              icon=UITool.getQIcon(":/ic_qq.png", self.APP_LOGO_SIZE, self.APP_LOGO_SIZE))

        self.btnPrePage.setFixedSize(25, 25)
        self.labelCurrentPage.setFixedSize(25, 25)
        self.labelCurrentPage.setAlignment(Qt.AlignCenter)
        self.btnNextPage.setFixedSize(25, 25)
        self.btnAddAccount.setFixedWidth(120)
        self.btnAddAccount.setFixedHeight(35)

        for i, btn in enumerate(self.toolBtnList):
            btn.clicked.connect(lambda state, idx=i: self.onToolBtnClicked(idx))

        self.btnRefresh.clicked.connect(lambda: self.controller.refreshData())
        self.btnNextPage.clicked.connect(lambda: self.__onPageChanged(True))
        self.btnPrePage.clicked.connect(lambda: self.__onPageChanged(False))
        self.btnAddAccount.clicked.connect(lambda: self.controller.addAccount())

        self.addAccountSignal.connect(self.controller.getLastPage)
        self.enableAddAccountSignal.connect(lambda: self.setAddAccountBtnEnabled(True))
        self.showMsgSignal.connect(self.showMsg)

        for toolBtn in self.toolBtnList:
            toolBtn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            toolBtn.setFixedHeight(60)
            toolBtn.setCheckable(True)

        # column: 0-9
        self.gridRoot.setColumnMinimumWidth(0, 35)
        self.gridRoot.setColumnMinimumWidth(1, 105)
        self.gridRoot.setColumnMinimumWidth(2, 105)
        self.gridRoot.setColumnMinimumWidth(3, 105)
        self.gridRoot.setColumnMinimumWidth(5, 65)
        self.gridRoot.setColumnMinimumWidth(6, 30)
        self.gridRoot.setColumnMinimumWidth(7, 30)
        self.gridRoot.setColumnMinimumWidth(8, 30)
        self.gridRoot.setColumnMinimumWidth(9, 35)

        # row: 0 - 5
        self.gridRoot.setRowMinimumHeight(0, 55)
        self.gridRoot.setRowMinimumHeight(1, 5)
        self.gridRoot.setRowMinimumHeight(2, 60)
        self.gridRoot.setRowMinimumHeight(4, 50)

        self.gridRoot.setColumnStretch(4, 1)
        self.gridRoot.setRowStretch(3, 1)
        self.gridRoot.setVerticalSpacing(0)
        self.gridRoot.setContentsMargins(0, 0, 0, 30)

        self.gridRoot.addWidget(self.labelTitle, 0, 1)
        self.gridRoot.addWidget(self.btnRefresh, 0, 8, Qt.AlignCenter)
        self.gridRoot.addWidget(self.widgetLine, 1, 0, 0, 10)
        self.gridRoot.addWidget(self.toolBtnWeCom, 2, 1)
        self.gridRoot.addWidget(self.toolBtnWechat, 2, 2, Qt.AlignCenter)
        self.gridRoot.addWidget(self.toolBtnQQ, 2, 3)
        self.gridRoot.addWidget(self.listUser, 3, 1, 1, 8)
        self.gridRoot.addWidget(self.labelPage, 4, 5, Qt.AlignCenter)
        self.gridRoot.addWidget(self.btnPrePage, 4, 6, Qt.AlignRight)
        self.gridRoot.addWidget(self.labelCurrentPage, 4, 7, Qt.AlignCenter)
        self.gridRoot.addWidget(self.btnNextPage, 4, 8, Qt.AlignLeft)
        self.gridRoot.addWidget(self.btnAddAccount, 2, 6, 1, 3)

        self.onToolBtnClicked(0)

    def onToolBtnClicked(self, dataType: int):
        self.appChangeSignal.emit(dataType)
        for toolBtn in self.toolBtnList:
            toolBtn.setChecked(False)
        self.toolBtnList[dataType].setChecked(True)

        self.controller.getData(1, dataType)

    def __onPageChanged(self, nextPage=True):
        self.controller.getData(self.controller.currentPage + 1 if nextPage else self.controller.currentPage - 1,
                                self.controller.dataType)

    def refreshList(self, dataList: List[Account], page: int, totalPage: int):
        self.listUser.clear()
        UITool.addListItem(self.listUser, TitleListItem(), 40)
        for i, data in enumerate(dataList):
            itemWidget = ListItem(data)
            UITool.addListItem(self.listUser, itemWidget, 50)
            itemWidget.setOnDecryptCallback(i, self.controller.decrypt_and_serialize)
            itemWidget.setOnActiveCallback(i, self.controller.active)
            itemWidget.setOnOpenDirCallback(i, self.controller.openDecryptedDir)

        self.labelPage.setText(f"共{totalPage}页")
        self.labelCurrentPage.setText(f"{page}")

    def onDecrypt(self, success: bool):
        pass

    def onActive(self, active: bool, success: bool, index: int):
        log.i("onActive", success)
        listWidget: ListItem = self.listUser.itemWidget(self.listUser.item(index + 1))
        listWidget.setBtnActiveUI(success)

    def setAddAccountBtnEnabled(self, enabled):
        self.btnAddAccount.setEnabled(enabled)

    def showMsg(self, typ, msg):
        if typ == 0:
            CustomMsgBox.showMsg(msg)
        elif typ == 1:
            CustomMsgBox.showToast(msg)
        else:
            CustomMsgBox.showStatus(msg)


class AbstractAccountListItem(BaseWidget):
    def __init__(self):
        super(AbstractAccountListItem, self).__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.hBox = QHBoxLayout(self)
        self.hBox.setContentsMargins(40, 0, 0, 0)
        self.setFixedHeight(self.getHeight())
        self.setLayout(self.hBox)

    @abstractmethod
    def getHeight(self) -> int:
        pass


class TitleListItem(AbstractAccountListItem):
    def __init__(self):
        super(TitleListItem, self).__init__()
        self.labelActiveTip = QLabel()
        self.__initView()

    def getHeight(self) -> int:
        return 40

    def __getQss(self) -> [dict, None]:
        return {self: "QLabel {font-size:18px; color:black}"
                      "QWidget {background-color:#dde3ed}"
                      "QToolTip {background-color: #000000; "
                      "border-radius:10px; "
                      "font-size: 15px;"
                      "color:white;"
                      "padding: 5px}",
                self.labelActiveTip: "border-image:url(:/ic_help.png)"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        self.hBox.addWidget(QLabel("账号信息"), 6, Qt.AlignLeft)
        self.hBox.addWidget(UITool.getLineFrame(1, "#c5d8ec", False))

        self.hBoxActive = HBoxLayoutWidget()
        self.hBoxActive.layout.addWidget(QLabel("密钥有效状态"), Qt.AlignCenter)

        self.labelActiveTip.setFixedSize(20, 20)
        self.labelActiveTip.enterEvent = lambda event: self.__showToolTip(True)
        self.labelActiveTip.leaveEvent = lambda event: self.__showToolTip(False)

        # self.hBoxActive.layout.addWidget(self.labelActiveTip)

        self.hBox.addWidget(self.hBoxActive, 4, Qt.AlignCenter)

    def __showToolTip(self, show=True):
        if show:
            self.labelActiveTip.setToolTip("激活状态是指当前帐号已经获取到了数据库密钥。")
            self.labelActiveTip.setToolTipDuration(30000)
        else:
            QToolTip.hideText()


class ListItem(AbstractAccountListItem):
    def __init__(self, account: Account):
        super(ListItem, self).__init__()

        self.account = account

        self.widgetProfile: CircleImage = CircleImage()
        self.labelAccount: QLabel = QLabel()
        self.btnDecrypt: QPushButton = QPushButton("解密")
        self.btnOpenDir: QPushButton = QPushButton("打开文件夹")

        self.labelOnline: QToolButton = QToolButton()

        self.btnActive: QPushButton = QPushButton()

        self.__initView()
        self.__loadData()

    def __getQss(self) -> [dict, None]:
        btnQssBlue = "QPushButton " \
              "{border:none; " \
              "border-radius:5px; " \
              "background-color: #dde3ed;" \
              "font-size: 15px" \
              "}"
        return {self: "QWidget {border-bottom: 1px solid #e0e4ed }",
                self.labelAccount: "font-size:16px; color:#494949",
                self.btnDecrypt: btnQssBlue,
                self.btnOpenDir: btnQssBlue,
                self.btnActive: "QPushButton {border:none; border-image:url(:/ic_toggle_off.png);}"
                                "QPushButton:checked {border:none; border-image:url(:/ic_toggle_on.png);}"}

    def __initView(self):
        UITool.setQss(self.__getQss())
        UITool.setCursor(Qt.PointingHandCursor, self.btnActive, self.btnDecrypt)

        self.btnDecrypt.setFixedSize(50, 25)
        self.btnDecrypt.setContentsMargins(10, 0, 10, 0)
        self.btnOpenDir.setFixedSize(100, 25)
        self.btnOpenDir.setContentsMargins(10, 0, 10, 0)
        # self.btnDecrypt.setVisible(True)
        self.btnActive.setFixedSize(50, 25)
        self.btnActive.setCheckable(True)

        accountWidget = QWidget()
        accountHBox = QHBoxLayout(accountWidget)
        accountHBox.setContentsMargins(0, 0, 0, 0)
        accountWidget.setLayout(accountHBox)

        self.widgetProfile.setFixedSize(30, 30)
        accountHBox.addWidget(self.widgetProfile)
        accountHBox.addWidget(self.labelAccount)
        accountHBox.addWidget(self.btnDecrypt)
        accountHBox.addWidget(self.btnOpenDir)
        accountHBox.addStretch(1)

        self.hBox.addWidget(accountWidget, 6)
        self.hBox.addWidget(UITool.getLineFrame(1, "#e0e4ed", False))
        self.hBox.addWidget(self.btnActive, 4, Qt.AlignCenter)

    def __loadData(self):
        self.widgetProfile.setImage(self.account.profile, 30, 30)
        self.labelAccount.setText(self.account.uid)
        self.setBtnActiveUI(self.account.active)

    def __onBtnActiveClicked(self, i, callback):
        self.btnActive.setChecked(self.account.active)
        callback(not self.account.active, i, self.account)

    def setBtnActiveUI(self, active: bool):
        self.account.active = active
        self.btnActive.setChecked(active)

    def getHeight(self) -> int:
        return 50

    def setOnDecryptCallback(self, i, callback):
        self.btnDecrypt.clicked.connect(lambda: callback(i, self.account))

    def setOnActiveCallback(self, i, callback):
        self.btnActive.clicked.connect(lambda: self.__onBtnActiveClicked(i, callback))

    def setOnOpenDirCallback(self, i, callback):
        self.btnOpenDir.clicked.connect(lambda: callback(self.account))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = AccountWidget()
    widget.show()
    sys.exit(app.exec_())
