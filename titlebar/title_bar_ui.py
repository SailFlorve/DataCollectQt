import sys

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QApplication, QToolButton, QGridLayout

from bean import constant
from util.tools import UITool
from widget.base_widget import BaseWidget


class TitleBar(BaseWidget):
    BUTTON_SIZE = 35
    BUTTON_ICON_SIZE = 25

    settingsClickedSignal = pyqtSignal(bool)

    def __init__(self, parent: [QWidget, None]):
        super(TitleBar, self).__init__()

        self.parent = self if parent is None else parent

        self.labelTitle = QLabel()
        self.labelIcon = QLabel()
        self.btnMinimize = QPushButton()
        self.btnClose = QPushButton()

        self.btnSettings = QPushButton()
        self.btnUser = QToolButton(self)

        self.__initView()

        UITool.enableDragMove(self, self.parent)

    def __getQss(self) -> [dict, None]:
        return {self: "QWidget {background-color: #2496ed;}"
                      "QLabel {font-size:16px;color:#FFFFFF;font-weight: bold;}",
                self.btnMinimize: """
                       QPushButton {
                           border-image: url(":/ic_minimize.png");
                           border: none;
                           }
                        
                           QPushButton:hover {
                           border-image: url(":/ic_minimize_hover.png");
                           border: none;
                       }""",
                self.btnClose: """
                       QPushButton {
                           border-image: url(":/ic_close_white.png");
                           border: none;
                           }
                           
                       QPushButton:hover {
                              border-image: url(":/ic_close_white_hover.png");
                              border: none;
                       }
                       """,
                self.btnSettings: "QPushButton {background-color: #1182d9;"
                                  "border:none;"
                                  "border-radius:17px;}"

                                  "QPushButton:checked {background-color: #ffffff;"
                                  "border:none;"
                                  "border-radius:17px;}",
                self.btnUser: "background-color:#1182d9;"
                              "border:none;"
                              "border-radius:17px;"
                              "color:white;"
                              "font-weight: bold;"
                              "font-size:15px;"
                              "padding:5px"}

    def __initView(self):
        UITool.setQss(self.__getQss())

        self.resize(800, 60)

        self.__initLabels()
        self.__initButtons()
        self.__initLayout()

    def __initLabels(self):
        self.labelIcon.setAlignment(Qt.AlignCenter)
        self.labelTitle.setAlignment(Qt.AlignCenter)
        UITool.setLabelStyle(self.labelIcon, size=QSize(40, 40), icon=":/ic_logo.png")
        UITool.setLabelStyle(self.labelTitle, text=constant.APP_NAME)

    def __initButtons(self):
        UITool.setButtonStyle(self.btnMinimize, size=QSize(self.BUTTON_SIZE - 10, self.BUTTON_SIZE - 10))
        UITool.setButtonStyle(self.btnClose, size=QSize(self.BUTTON_SIZE - 10, self.BUTTON_SIZE - 10))

        self.btnClose.clicked.connect(self.parent.close)
        self.btnMinimize.clicked.connect(self.parent.showMinimized)

        self.btnSettings.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.btnSettings.setIcon(
            UITool.getQIcon(":/ic_setting_white.png", self.BUTTON_ICON_SIZE, self.BUTTON_ICON_SIZE))
        self.btnSettings.setCheckable(True)
        self.btnSettings.clicked.connect(self.onSettingsClicked)

        UITool.setCursor(Qt.PointingHandCursor, self.btnSettings, self.btnUser)

        self.btnUser.setFixedSize(90, self.BUTTON_SIZE)
        self.btnUser.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btnUser.setIcon(UITool.getQIcon(":/ic_user.png", self.BUTTON_ICON_SIZE, self.BUTTON_ICON_SIZE))
        self.btnUser.setText("admin")

    def __initLayout(self):
        gridLayout = UITool.getLayout(QGridLayout(self), self, (35, 0, 35, 0))

        titleWidget = QWidget()
        hBoxTitle = UITool.getLayout(QHBoxLayout(), titleWidget, spacing=5)
        hBoxTitle.addWidget(self.labelIcon)
        hBoxTitle.addWidget(self.labelTitle)

        gridLayout.addWidget(titleWidget, 0, 1, Qt.AlignCenter)

        btnWidget = QWidget()
        hBoxBtn = UITool.getLayout(QHBoxLayout(), btnWidget, spacing=10)
        hBoxBtn.addWidget(self.btnSettings)
        hBoxBtn.addWidget(self.btnUser)
        hBoxBtn.addWidget(self.btnMinimize)
        hBoxBtn.addWidget(self.btnClose)

        gridLayout.addWidget(btnWidget, 0, 2, Qt.AlignRight)

        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        gridLayout.setColumnStretch(2, 1)

        self.setLayout(gridLayout)

    def onSettingsClicked(self):
        checked = self.btnSettings.isChecked()
        if checked:
            self.btnSettings.setIcon(
                UITool.getQIcon(":/ic_setting_blue.png", self.BUTTON_ICON_SIZE, self.BUTTON_ICON_SIZE))
        else:
            self.btnSettings.setIcon(
                UITool.getQIcon(":/ic_setting_white.png", self.BUTTON_ICON_SIZE, self.BUTTON_ICON_SIZE))

        self.settingsClickedSignal.emit(checked)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    title_bar = TitleBar(None)
    title_bar.show()
    sys.exit(app.exec_())
