import hashlib
import json
import mimetypes
import os
import pathlib
import time
from os import PathLike
from typing import Dict, Tuple, AnyStr, Any, List

from PyQt5 import QtGui
from PyQt5.QtCore import QSize, QFile, Qt
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QColor
from PyQt5.QtWidgets import QLabel, QWidget, QAbstractButton, QFrame, QListWidget, QListWidgetItem, QLayout, \
    QGraphicsDropShadowEffect
from win32comext.shell.shell import ShellExecuteEx

import resources.resources_rc
from util import log, magic
from util.cpp_lib import CppLibrary

log.i(resources.resources_rc.qt_version)

fileHeaderBytesDict = {
    # "ffd8": ".jpeg",
    # "8950": ".png",
    # "4749": ".gif",
    # "504b": ".zip",
    # "2550": ".pdf",
    # "0000": ".mp4",
    "0223": ".slk"
}


class UITool:
    @staticmethod
    def getQIcon(path: str, w, h) -> QIcon:
        qIcon = QIcon()
        pixmap = QPixmap()
        pixmap.load(path)
        pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio)
        qIcon.addPixmap(pixmap)
        return qIcon

    @staticmethod
    def setButtonStyle(btn: QAbstractButton, size: QSize = None, text: str = None, icon: QIcon = None, qss: str = None):
        if text is not None:
            btn.setText(text)
        if size is not None:
            btn.setFixedSize(size)
        if qss is not None:
            btn.setStyleSheet(qss)
        if icon is not None:
            btn.setIcon(icon)

    @staticmethod
    def setLabelStyle(label: QLabel, text: str = None, icon: str = None,
                      size: QSize = None, qss: str = None):
        if text is not None:
            label.setText(text)
        if icon is not None:
            pixmap = QPixmap()
            pixmap.load(icon)
            if size is not None:
                pixmap = pixmap.scaled(size.width(), size.height(), Qt.KeepAspectRatio)
            label.setPixmap(pixmap)
        if size is not None:
            label.setFixedSize(size)
        if qss is not None:
            label.setStyleSheet(qss)

    @staticmethod
    def loadQss(w: QWidget, qssPath: str):
        qss_file = QFile(qssPath)
        qss_file.open(QFile.ReadOnly)
        qss = str(qss_file.readAll(), encoding='utf-8')
        qss_file.close()
        w.setStyleSheet(qss)

    @staticmethod
    def setQss(qssDict: Dict[QWidget, str]):
        for widget, qss in qssDict.items():
            widget.setStyleSheet(qss)

    @staticmethod
    def getLineFrame(width: int, color: str, horizontal: bool = True):

        lineFrame = QFrame()
        lineFrame.setFrameShape(QFrame.HLine if horizontal else QFrame.VLine)
        lineFrame.setLineWidth(width)
        if horizontal:
            lineFrame.setFixedHeight(1)
        else:
            lineFrame.setFixedWidth(1)
        lineFrame.setStyleSheet("""
            QFrame[frameShape="4"]
            {
                color: %s;
            }
            
            QFrame[frameShape="5"]
            {
                color: %s;
            }
        """ % (color, color))
        return lineFrame

    @staticmethod
    def addListItem(listWidget: QListWidget, itemWidget: QWidget, height: int):
        item = QListWidgetItem()
        item.setSizeHint(QSize(1, height))
        listWidget.addItem(item)
        listWidget.setItemWidget(item, itemWidget)

    @staticmethod
    def setCursor(cursorType: int, *args: QWidget):
        for w in args:
            w.setCursor(QCursor(cursorType))

    @staticmethod
    def getLayout(layout: QLayout, parent: QWidget, margins: Tuple = (0, 0, 0, 0), spacing: int = 0):
        layout.setParent(parent)
        parent.setLayout(layout)
        layout.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        layout.setSpacing(spacing)
        return layout

    @staticmethod
    def getWidgetPos(widget: QWidget, layout: QWidget, globalPos=False):
        return widget.mapToGlobal(widget.rect().topLeft()) if globalPos \
            else widget.mapTo(layout, widget.rect().topLeft())

    @staticmethod
    def getSuperLinkHtml(linkDict: Dict[str, str], sep=" "):
        # <a href = ""> text </a>
        result = ""
        for text, href in linkDict.items():
            result += f"<a href=\"{href}\">{text}</a>{sep}"
        return result

    @staticmethod
    def setShadow(w: QWidget):
        effect = QGraphicsDropShadowEffect(w)
        effect.setOffset(0, 0)
        effect.setColor(QColor(0, 0, 0, 90))
        effect.setBlurRadius(15)
        w.setGraphicsEffect(effect)

    @staticmethod
    def generateVersionList(*args: Tuple) -> List[Dict[str, str]]:
        result = []
        for t in args:
            result.append({"version": t[0], "link": t[1]})
        return result

    @staticmethod
    def enableDragMove(wDrag: QWidget, wMove: QWidget = None):
        if wMove is None:
            wMove = wDrag

        wDrag.__mouseX = 0
        wDrag.__mouseY = 0
        wDrag.__lastX = 0
        wDrag.__lastY = 0

        def mousePressEvent(a0: QtGui.QMouseEvent) -> None:
            wDrag.__mouseX = a0.globalX()
            wDrag.__mouseY = a0.globalY()

            wDrag.__lastX = wMove.x()
            wDrag.__lastY = wMove.y()

        def mouseMoveEvent(a0: QtGui.QMouseEvent) -> None:
            moveX = a0.globalX() - wDrag.__mouseX
            moveY = a0.globalY() - wDrag.__mouseY

            newX = wDrag.__lastX + moveX
            newY = wDrag.__lastY + moveY

            wMove.move(newX, newY)

        wDrag.mousePressEvent = mousePressEvent
        wDrag.mouseMoveEvent = mouseMoveEvent


class MD5Tool:
    @staticmethod
    def getMD5(string: str):
        md5 = hashlib.md5()
        md5.update(string.encode("utf-8"))
        strMd5 = md5.hexdigest()
        return strMd5


class WinTool:
    @staticmethod
    def isProcessExists(name: str) -> [bool, int]:
        lib = CppLibrary()
        pid = lib.findProcessId(name)
        return pid != 0, pid

    @staticmethod
    def openExecute(path: str):
        if path[0] != '"':
            path = f'"{path}"'
        # appPath = r"C:\Users\Hang\Desktop\admin.bat"
        log.i(f"open {path}")
        command: str = f'start "" {path}'
        log.i(command)
        ShellExecuteEx(lpVerb='runas', lpFile='cmd.exe', lpParameters='/c ' + command)

    @staticmethod
    def killProcess(processName: str):
        os.system(f"taskkill /F /IM {processName}")

    @staticmethod
    def openDir(dirPath: PathLike[str]):
        # 弹出资源管理器
        os.startfile(dirPath)


class Utility:

    @staticmethod
    def getJsonStr(obj):
        return json.dumps(obj, ensure_ascii=False, indent=4)

    @staticmethod
    def getFileExtByBytes(fileBytes: bytes) -> str:
        mime = magic.from_buffer(fileBytes, mime=True)

        if mime == "application/octet-stream":
            if fileBytes[0:2].hex() in fileHeaderBytesDict:
                return fileHeaderBytesDict[fileBytes[0:2].hex()]

        ext = mimetypes.guess_extension(mime)
        if ext is None:
            ext = ""
        return ext

    @staticmethod
    def readFileAndWrite(filePath, offset, length, outputPath):
        with open(filePath, 'rb') as fr:
            fr.seek(offset, 0)
            content = fr.read(length)

            with open(outputPath, 'wb+') as fw:
                fw.write(content)

    @staticmethod
    def readFile(filePath: PathLike, offset, length) -> bytes:
        with open(filePath, 'rb') as fr:
            fr.seek(offset, 0)
            content = fr.read(length)
        return content

    @staticmethod
    def writeFile(outputPath: PathLike, content: AnyStr, autoExt=False):

        if autoExt:
            ext: str = Utility.getFileExtByBytes(content)
            outputPath = str(outputPath) + ext

        pathlib.Path(outputPath).write_bytes(content)

    @staticmethod
    def findTabInXml(xml: str, tab: str):
        tabStart = f"<{tab}>"
        tabEnd = f"</{tab}>"
        tabStartIdx = xml.find(tabStart)
        tabEndIdx = xml.find(tabEnd)
        return xml[tabStartIdx + len(tabStart): tabEndIdx]

    @staticmethod
    def addListInDict(d: Dict[Any, List[Any]], key, value):
        if key not in d:
            d[key] = [value]
        else:
            d[key].append(value)

    @staticmethod
    def getFormatTime(timestamp: float) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    @staticmethod
    def getMillisecondTime() -> float:
        return time.time() * 1000


if __name__ == '__main__':
    import win32api
    import win32con

    filename = r"D:\apps\Axure\AxureRP_9.0.0.3714_Green\Axure RP\Bin\AxureRP9.exe"

    # 获取文件的属性
    attributes = win32api.GetFileAttributes(filename)
    print(attributes)
