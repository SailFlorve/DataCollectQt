from abc import abstractmethod

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class BaseWidget(QWidget):
    def __init__(self):
        super(BaseWidget, self).__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)

    @abstractmethod
    def __getQss(self) -> [dict, None]:
        pass

    @abstractmethod
    def __initView(self):
        pass
