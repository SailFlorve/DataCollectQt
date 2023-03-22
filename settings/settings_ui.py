import os.path
import os.path
import sys
from abc import abstractmethod
from typing import List

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QStackedWidget, QToolButton, QListWidget, QApplication, \
    QHBoxLayout

from bean.beans import SocialConfig, AppTypeToName
from util import log, app_download_info
from util.tools import UITool
from widget.base_widget import BaseWidget
from widget.custom_msgbox import CustomMsgBox
from widget.layout_widget import HBoxLayoutWidget, VBoxLayoutWidget


class BaseSettingsWidget(BaseWidget):
    def __init__(self):
        from settings.settings_controller import SettingsController
        super(BaseSettingsWidget, self).__init__()
        self.controller = SettingsController(self)

    @abstractmethod
    def __initView(self):
        pass

    @abstractmethod
    def __getQss(self) -> [dict, None]:
        pass

    def showOnFilePathChange(self, path: str, typ: int):
        log.i(path, typ)
        CustomMsgBox.showToast("修改成功")


class SettingsWidget(BaseSettingsWidget):
    def __init__(self):
        super(SettingsWidget, self).__init__()

        self.labelTitle = QLabel("系统设置")
        self.btnClose = QPushButton()

        self.btnCommonSettings = QPushButton("通用配置")
        self.btnSocialSettings = QPushButton("社交平台配置")
        self.btnSettingsList = [self.btnCommonSettings, self.btnSocialSettings]

        self.stackedWidget = QStackedWidget()

        self.__initView()

        self.__onPageBtnClicked(0)

    def __getQss(self) -> [dict, None]:
        qssBtn = "QPushButton {font-size:17px; " \
                 "color:#636b71; " \
                 "border:none;background-color:transparent;" \
                 "text-align:left; " \
                 "padding-left:15px }" \
                 "QPushButton:checked {background-color:#d8eaf6; border:0px; border-left:2px solid #007bff; }"
        return {self: "background-color:#f4f4f6",
                self.labelTitle: "font-size:20px",
                self.btnClose: "border:none",
                self.btnCommonSettings: qssBtn,
                self.btnSocialSettings: qssBtn}

    def __initView(self):
        UITool.setQss(self.__getQss())
        vBoxRoot = UITool.getLayout(QVBoxLayout(), self)
        self.btnClose.setIcon(UITool.getQIcon(":/ic_close_gray", 16, 16))
        self.btnClose.setFixedSize(25, 25)

        UITool.setCursor(Qt.PointingHandCursor, self.btnClose, self.btnCommonSettings, self.btnSocialSettings)

        for i, btn in enumerate(self.btnSettingsList):
            btn.setFixedSize(165, 45)
            btn.setCheckable(True)
            btn.clicked.connect(lambda state, idx=i: (self.__onPageBtnClicked(idx)))

        widgetTitle = HBoxLayoutWidget(margins=(35, 0, 35, 0))
        widgetTitle.layout.addWidget(self.labelTitle)
        widgetTitle.layout.addStretch(1)
        widgetTitle.layout.addWidget(self.btnClose)
        widgetTitle.setFixedHeight(55)

        widgetBtn = VBoxLayoutWidget(spacing=15, margins=(0, 30, 25, 0))
        widgetBtn.layout.addWidget(self.btnCommonSettings)
        widgetBtn.layout.addWidget(self.btnSocialSettings)
        widgetBtn.layout.addStretch(1)

        widgetContent = HBoxLayoutWidget(margins=(35, 0, 35, 0))
        widgetContent.layout.addWidget(widgetBtn)
        widgetContent.layout.addWidget(UITool.getLineFrame(1, "#d6d6d8", False))
        widgetContent.layout.addWidget(self.stackedWidget, 1)

        self.stackedWidget.setContentsMargins(30, 30, 30, 30)
        self.stackedWidget.addWidget(CommonSettingsWidget())
        self.stackedWidget.addWidget(SocialSettingsWidget())

        vBoxRoot.addWidget(widgetTitle)
        vBoxRoot.addWidget(UITool.getLineFrame(1, "#d6d6d8"))
        vBoxRoot.addWidget(widgetContent)

    def __onPageBtnClicked(self, index: int):
        for btn in self.btnSettingsList:
            btn.setChecked(False)

        self.btnSettingsList[index].setChecked(True)
        self.stackedWidget.setCurrentIndex(index)


class CommonSettingsWidget(BaseSettingsWidget):
    def __init__(self):
        super(CommonSettingsWidget, self).__init__()

        self.vBoxRoot: QVBoxLayout = UITool.getLayout(QVBoxLayout(), self, spacing=20)
        self.labelFileStorage = QLabel("文件存储")
        self.labelFilePath = QLabel()
        self.labelDes = QLabel("文件默认保存位置")
        self.btnChange = QPushButton("更改")

        self.__initView()

    def __getQss(self) -> [dict, None]:
        return {self.labelFileStorage: "font-size:18px;",
                self.labelFilePath: "color:#c0c0c0;"
                                    "border:none;"
                                    "border-bottom:2px solid #b5b5b6;"
                                    "padding-bottom:8px;"
                                    "font-size:18px ",
                self.labelDes: "color:#c0c0c0; font-size:18px",
                self.btnChange: "background-color:#ffffff; "
                                "border: 1px solid #b5b5b6; "
                                "border-radius:5px;"
                                "font-size:15px"}

    def __initView(self):
        UITool.setQss(self.__getQss())
        self.btnChange.setFixedSize(70, 30)
        self.btnChange.clicked.connect(lambda: self.controller.changeFilePath(SocialConfig.DEFAULT))

        self.showOnFilePathChange(self.controller.getDefaultFilePath(), SocialConfig.DEFAULT)

        self.vBoxRoot.addWidget(self.labelFileStorage)
        self.vBoxRoot.addWidget(self.labelFilePath)
        self.vBoxRoot.addWidget(self.labelDes)
        self.vBoxRoot.addWidget(self.btnChange)
        self.vBoxRoot.addStretch(1)

    def showOnFilePathChange(self, path: str, typ: int):
        self.labelFilePath.setText(os.path.expandvars(path))


class SocialSettingsWidget(BaseSettingsWidget):
    def __init__(self):
        super(SocialSettingsWidget, self).__init__()
        self.labelTitle = QLabel("平台列表")
        self.descriptionLabel: QLabel = QLabel()
        self.settings: List[SocialConfig]
        self.__initView()

    def __getQss(self) -> [dict, None]:
        return {self: "QLabel {color:#687176; font-size:20px}"
                      "QListWidget {background-color:transparent;border:none}"
                      "QLabel#descriptionLabel {font-size:16px}"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        vBox: QVBoxLayout = UITool.getLayout(QVBoxLayout(), self, spacing=20)
        listPlatform: QListWidget = QListWidget()
        self.descriptionLabel.setObjectName("descriptionLabel")

        self.settings = self.controller.getSettings()

        for i in range(len(self.settings) + 1):
            UITool.addListItem(listPlatform,
                               SettingItemWidget(None if i == 0 else self.settings[i - 1], self.controller),
                               40 if i == 0 else 50)

        self.__refreshDescriptions()

        vBox.addWidget(self.labelTitle)
        vBox.addWidget(listPlatform)
        vBox.addWidget(self.descriptionLabel)

    def __refreshDescriptions(self):
        text = "存储路径: \n"
        for socialConfig in self.settings:
            text += f"{AppTypeToName[socialConfig.type]}: " \
                    f"{'默认' if len(socialConfig.path) == 0 else socialConfig.path}\n"
        text += "\n"
        text += app_download_info.getDescription()
        self.descriptionLabel.setText(text)

    def showOnFilePathChange(self, path: str, typ: int):
        self.settings[typ].path = path
        self.__refreshDescriptions()


class SettingItemWidget(BaseWidget):
    def __init__(self, config: SocialConfig, controller):
        from settings.settings_controller import SettingsController
        super(SettingItemWidget, self).__init__()
        self.controller: SettingsController = controller
        self.btnName = QToolButton()
        self.btnStatus = QToolButton()
        self.btnEdit = QPushButton()
        self.labelVersion = QLabel()

        self.labelList = []

        self.widgetHBox: QHBoxLayout = UITool.getLayout(QHBoxLayout(), self)

        self.config = config
        self.__initView()

    def __getQss(self) -> [dict, None]:
        return {self: "QWidget {border-bottom: 1px solid #e1e5ed }"
                      "QLabel {font-size: 18px }"
                      "QAbstractButton {border: none;font-size:15px},",
                self.btnStatus: "color:#999999;",
                self.labelVersion: "background-color:transparent"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        if self.config is None:
            widgetList = [QLabel("平台名称"), QLabel("状态"), QLabel("存储路径"), QLabel("支持版本")]
            self.labelList = widgetList
            self.setStyleSheet("background-color:#dde3ed; font-size:16px")
        else:
            nameList = ["企业微信", "微信", "QQ"]
            iconList = [":/ic_buswechat.png", ":/ic_wechat.png", ":/ic_qq.png"]

            self.btnName.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.btnStatus.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

            UITool.setButtonStyle(self.btnName, QSize(90, 20), text=nameList[self.config.type],
                                  icon=UITool.getQIcon(iconList[self.config.type], 25, 25))

            status = self.config.status
            iconPath = ":/ic_running.png" if status else ":/ic_not_running.png"
            UITool.setButtonStyle(self.btnStatus, QSize(70, 20), text="已授权" if status else "未授权",
                                  icon=UITool.getQIcon(iconPath, 10, 10))

            self.btnEdit.setIcon(UITool.getQIcon(":/ic_edit.png", 16, 16))
            self.btnEdit.clicked.connect(lambda: self.controller.changeFilePath(self.config.type))
            UITool.setCursor(Qt.PointingHandCursor, self.btnEdit, self.labelVersion)
            self.labelVersion.setText(str(self.config.versions))
            self.labelVersion.setOpenExternalLinks(True)

            widgetList = [self.btnName, self.btnStatus, self.btnEdit, self.labelVersion]

        self.widgetHBox.addWidget(widgetList[0], 150, Qt.AlignCenter)
        lineColor = "#c2d4e6" if self.config is None else "#e1e5ed"
        self.widgetHBox.addWidget(UITool.getLineFrame(2, lineColor, False))
        self.widgetHBox.addWidget(widgetList[1], 115, Qt.AlignCenter)
        self.widgetHBox.addWidget(UITool.getLineFrame(2, lineColor, False))
        self.widgetHBox.addWidget(widgetList[2], 95, Qt.AlignCenter)
        self.widgetHBox.addWidget(UITool.getLineFrame(2, lineColor, False))
        self.widgetHBox.addWidget(widgetList[3], 270, Qt.AlignCenter)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SettingsWidget()
    w.resize(900, 600)
    w.show()

    sys.exit(app.exec_())
