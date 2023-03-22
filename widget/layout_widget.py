from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout

from util.tools import UITool


class LayoutWidget(QWidget):
    def __init__(self, parent):
        super(LayoutWidget, self).__init__(parent)

    def _getLayout(self, layout, margins=(0, 0, 0, 0), spacing=0):
        return UITool.getLayout(layout, self, margins, spacing)


class HBoxLayoutWidget(LayoutWidget):
    def __init__(self, parent=None, margins=(0, 0, 0, 0), spacing=0):
        super(HBoxLayoutWidget, self).__init__(parent)
        self.layout: QHBoxLayout = self._getLayout(QHBoxLayout(), margins, spacing)
        if parent is not None:
            parent.setLayout(self.layout)


class VBoxLayoutWidget(LayoutWidget):
    def __init__(self, parent=None, margins=(0, 0, 0, 0), spacing=0):
        super(VBoxLayoutWidget, self).__init__(parent)
        self.layout: QVBoxLayout = self._getLayout(QVBoxLayout(), margins, spacing)
        if parent is not None:
            parent.setLayout(self.layout)


class GridLayoutWidget(LayoutWidget):
    def __init__(self, parent=None, margins=(0, 0, 0, 0), spacing=0):
        super(GridLayoutWidget, self).__init__(parent)
        self.layout: QGridLayout = self._getLayout(QGridLayout(), margins, spacing)
        if parent is not None:
            parent.setLayout(self.layout)
