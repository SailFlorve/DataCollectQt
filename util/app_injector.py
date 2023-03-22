"""
负责注入获取Key，并用Key解密
Pywin32必须使用pip
"""

import os
import pathlib
import time
import winreg
from abc import abstractmethod
from typing import Callable, Dict

import pywintypes
import win32file
import win32pipe
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import QFileDialog

from bean.beans import Account, SocialConfig, AppList
from util import log
from util.cpp_lib import CppLibrary
from util.tools import WinTool

pathDict: Dict[int, str] = {}  # path是不带“”的

dllInjectDict = {SocialConfig.WECOM: r".\lib\WeComHookDLL.dll",
                 # SocialConfig.WECHAT: r"D:\Projects\VSProjects\DataCollectCpp\debug\WeChatHookDLL.dll",
                 SocialConfig.WECHAT: r".\lib\WeChatHookDLL.dll",
                 SocialConfig.QQ: r".\lib\QQHookDLL.dll"}

pipeNameDict = {SocialConfig.WECOM: "\\\\.\\pipe\\WECOM_TEMP",
                SocialConfig.WECHAT: "\\\\.\\pipe\\WECHAT_TEMP",
                SocialConfig.QQ: "\\\\.\\pipe\\QQ_TEMP"}

processDict = {SocialConfig.WECOM: "WXWork.exe",
               SocialConfig.WECHAT: "WeChat.exe",
               SocialConfig.QQ: "QQ.exe"}

messageReceiveThread = QThread()
injectThread = QThread()

displayNameList = []


def generatePathDict():
    subKeyList = [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                  r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall']

    for subKey in subKeyList:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subKey, 0, winreg.KEY_ALL_ACCESS)
        for j in range(0, winreg.QueryInfoKey(key)[0]):
            try:
                keyName = winreg.EnumKey(key, j)
                keyPath = subKey + '\\' + keyName
                eachKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, keyPath, 0, winreg.KEY_ALL_ACCESS)
                DisplayName, REG_SZ = winreg.QueryValueEx(eachKey, 'DisplayName')
                DisplayIcon, REG_SZ = winreg.QueryValueEx(eachKey, 'DisplayIcon')
                displayNameList.append(DisplayName)
                if DisplayName in AppList:
                    pathDict[AppList[DisplayName]] = DisplayIcon.replace('"', "")

            except WindowsError:
                pass


class AppInjector(QObject):
    def __init__(self, appType: int):
        super(AppInjector, self).__init__()
        self.appType = appType
        self.cppLib = CppLibrary()

        # 用于注入DLL结果回调
        self.injectCallback: Callable[[int, str], None] = Callable[[int, str], None]
        # 当接收到管道消息后回调
        self.onMessageReceiveListener: Callable[[bool, int, Account], None] = Callable[[bool, int, Account], None]
        # 当程序被关闭后回调
        self.onAppExitCallback: Callable[[], None] = Callable[[], None]
        # 需要弹出对话框时回调
        self.showMsgCallback: Callable[[int, str], None] = Callable[[int, str], None]
        # 当获取到app安装路径时回调
        self.onGetAppInstallPathCallback: Callable[[int, str], None] = Callable[[int, str], None]

        self.decryptThread = None

        self.isMsgReceived = False

    @staticmethod
    def getInjector(appType: int) -> 'AppInjector':
        if appType == SocialConfig.WECOM:
            return WeComInjector(appType)
        elif appType == SocialConfig.WECHAT:
            return WeChatInjector()
        elif appType == SocialConfig.QQ:
            return QQInjector()

    def _open(self, injectCallback) -> bool:
        processName = processDict[self.appType]
        WinTool.killProcess(processName)

        # 检测残留进程
        for i in range(10):
            if self.cppLib.findProcessId(processName) == 0:
                break
            time.sleep(0.1)

        if self.cppLib.findProcessId(processName) != 0:
            injectCallback(1, f"检测到进程残留，请手动结束{processName}或稍后再试。")
            return False

        if len(pathDict) == 0:
            generatePathDict()
        if self.appType in pathDict:
            appPath = pathDict[self.appType]
            WinTool.openExecute(appPath)
            return True
        else:
            log.i(f"open failed, current app list: {displayNameList}")
            self.showMsgCallback(1, "没有找到此程序，请手动选择路径。")
            filePath, _ = QFileDialog.getOpenFileName(None, "选择路径",
                                                      os.path.expandvars("%userprofile%/desktop"),
                                                      f"主程序 ({processDict[self.appType]})")
            if filePath == "":
                injectCallback(1, "没有找到此程序。")
                return False
            else:
                WinTool.openExecute(filePath)
                return True

    def inject(self, injectCallback: Callable[[int, str], None],
               messageReceiveListener: Callable[[bool, int, Account], None],
               appExitCallback: Callable[[], None]):

        self.injectCallback = injectCallback
        self.onMessageReceiveListener = messageReceiveListener
        self.onAppExitCallback = appExitCallback

        if not pathlib.Path(dllInjectDict[self.appType]).exists():
            injectCallback(1, f"注入DLL: {dllInjectDict[self.appType]}不存在！")
            return

        openRes = self._open(injectCallback)
        if not openRes:
            return

        global injectThread
        injectThread = QThread()
        injectThread.run = self._injectInternal
        injectThread.start()

    @abstractmethod
    def _injectInternal(self):
        pass

    def _closePipeAndWait(self):
        # （没有收到消息）但程序被关闭，结束管道
        try:
            win32file.DeleteFile(pipeNameDict[self.appType])
        except pywintypes.error as e:
            log.i(e)
        # 进程结束后 由此线程等待receive线程
        messageReceiveThread.wait()
        self.onAppExitCallback()
        log.i("Inject thread terminated.")

    def receiveMessage(self):
        global messageReceiveThread
        messageReceiveThread = QThread()
        messageReceiveThread.run = self._receiveMessageInternal
        messageReceiveThread.start()

    # 子线程
    def _receiveMessageInternal(self):
        import pydevd
        try:
            pydevd.settrace(suspend=False)
        except ConnectionRefusedError:
            pass
        time.sleep(1)

        pipeHandle = win32file.INVALID_HANDLE_VALUE
        while pipeHandle == win32file.INVALID_HANDLE_VALUE:
            try:
                pipeHandle = win32pipe.CreateNamedPipe(
                    pipeNameDict[self.appType],
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1,
                    1024 * 16,
                    1024 * 16,
                    win32pipe.NMPWAIT_USE_DEFAULT_WAIT,
                    None
                )
            except pywintypes.error as e:
                log.i(e)
            time.sleep(0.2)

        log.i("Wait for connect... ", self.appType, pipeNameDict[self.appType])
        win32pipe.ConnectNamedPipe(pipeHandle, None)
        self.isMsgReceived = True
        try:
            content = win32file.ReadFile(pipeHandle, 4096, None)  # 这里的4096要和C++的WriteFile中的参数一致
            time.sleep(1)
            if content is None:
                log.i("data is none")
                return
            else:
                contentStr = content[1].decode("utf-8")
                log.i("OriginData:\n", contentStr)
                res, account = self._resolveMessage(contentStr)

                if self.onMessageReceiveListener is not None:
                    self.onMessageReceiveListener(res, self.appType, account)

            # 接收到消息后 由此线程结束inject线程，Inject线程一般还在死循环
            injectThread.terminate()
        except pywintypes.error as e:
            log.i(e)

        log.i("Connect finish.")
        win32pipe.DisconnectNamedPipe(pipeHandle)
        win32file.CloseHandle(pipeHandle)
        log.i("ReceiveMessageInternal finish.")

    def _resolveMessage(self, content: str) -> [bool, Account]:
        msgArr = content.split("\n")
        status = msgArr[0]

        if status != "SUCCESS":
            return False, None

        path = msgArr[1]
        userId = msgArr[2]
        bakKey = msgArr[3]
        profile = msgArr[4] if len(msgArr[4]) > 10 else ":/ic_logo.png"

        account = Account(userId, profile, self.appType, True, "", bakKey, int(time.time()), path)

        return True, account


class WeChatInjector(AppInjector):
    def __init__(self):
        super(WeChatInjector, self).__init__(SocialConfig.WECHAT)

    def _injectInternal(self):
        processName = processDict[self.appType]
        dllPath = dllInjectDict[self.appType]
        dllPath = str(pathlib.Path(dllPath).resolve())
        pid = self.cppLib.findProcessId(processName)
        findProcessTime = 0
        # 轮询进程pid pid不为0说明打开了
        while pid == 0:
            findProcessTime += 1
            if findProcessTime == 50:
                self.injectCallback(1, "未找到进程")
                return
            pid = self.cppLib.findProcessId(processName)
            time.sleep(0.1)

        self.cppLib.inject(pid, dllPath, self.injectCallback)

        self.onGetAppInstallPathCallback(self.appType, pathDict[self.appType])

        pid = self.cppLib.findProcessId(processName)

        # 当微信运行时，此处死循环
        while pid != 0:
            time.sleep(0.2)
            pid = self.cppLib.findProcessId(processName)

        self._closePipeAndWait()

    def _resolveMessage(self, content: str) -> [bool, Account]:
        res, account = super()._resolveMessage(content)
        if not pathlib.Path(account.profile).exists():
            account.profile = ":/ic_wechat_profile.png"
        return res, account


class QQInjector(AppInjector):
    def __init__(self):
        super(QQInjector, self).__init__(SocialConfig.QQ)

    def _open(self, injectCallback) -> bool:
        if len(pathDict) == 0:
            generatePathDict()

        filePath, _ = QFileDialog.getOpenFileName(None, "选择QQ路径",
                                                  os.path.expandvars("%userprofile%/desktop"),
                                                  "QQ主程序 (腾讯QQ.lnk; QQ.lnk; QQ.exe; QQScLauncher.exe)")

        if filePath == "":
            injectCallback(1, "没有选择路径。")
            return False
        else:
            pathDict[self.appType] = filePath

            return super()._open(injectCallback)

    def _injectInternal(self):
        processName = processDict[self.appType]
        dllPath = dllInjectDict[self.appType]
        dllPath = str(pathlib.Path(dllPath).resolve())

        allCount = 0
        num2Count = 0

        while True:
            time.sleep(0.1)
            allCount += 1
            if allCount > 100:
                self.injectCallback(1, "注入超时，请重试。")
                WinTool.killProcess(processName)
                return
            num, pids = self.cppLib.findProcessIds(processName)
            log.i("QQ Process Num:", num, "Pids:", pids)
            if num != 2:
                continue
            else:
                num2Count += 1
                if num2Count <= 10:
                    continue
                # thCnt = self.cppLib.getProcessThreadCount(processName)
                # log.i("Thread Count:", thCnt)
                # if len(thCnt) != 2 or thCnt[0] == thCnt[1]:
                #     continue
                # time.sleep(0.5)
                # index = thCnt.index(min(thCnt))
                # log.i("Ready to inject index", index, "Pid", pids[index])
                self.cppLib.inject(pids[1], dllPath, self.injectCallback)
                break

        self.onGetAppInstallPathCallback(self.appType, pathDict[self.appType])

        # 已注入，监控进程个数
        msgShowed = False
        num, pids = self.cppLib.findProcessIds(processName)
        while num != 0:
            time.sleep(0.3)
            num, pids = self.cppLib.findProcessIds(processName)
            if num == 2:
                continue
            else:
                if not self.isMsgReceived and not msgShowed:
                    msgShowed = True
                    self.showMsgCallback(0, "请手动点击QQ主界面菜单选项中的“聊天记录备份与恢复”。")

        self.showMsgCallback(1, "操作取消。")
        self._closePipeAndWait()

    def _resolveMessage(self, content: str):
        self.showMsgCallback(1, "成功。")
        res, account = super()._resolveMessage(content)
        account.profile = ":/ic_qq_profile.png"
        return res, account


class WeComInjector(AppInjector):
    def _injectInternal(self):
        processName = processDict[self.appType]
        dllPath = dllInjectDict[self.appType]
        dllPath = str(pathlib.Path(dllPath).resolve())
        pid = self.cppLib.findProcessId(processName)
        findProcessTime = 0
        # 轮询进程pid pid不为0说明打开了
        while pid == 0:
            print("pid", pid)
            findProcessTime += 1
            if findProcessTime == 50:
                self.injectCallback(1, "未找到进程")
                return
            pid = self.cppLib.findProcessId(processName)
            time.sleep(0.1)

        self.cppLib.inject(pid, dllPath, self.injectCallback)
        self.showMsgCallback(1, "若为首次登录企业微信，则消息解密可能不完整，重新添加相同账号即可。")

        self.onGetAppInstallPathCallback(self.appType, pathDict[self.appType])
        pid = self.cppLib.findProcessId(processName)
        # 当运行时，此处死循环
        while pid != 0:
            time.sleep(0.5)
        pid = self.cppLib.findProcessId(processName)

        self._closePipeAndWait()

    def _resolveMessage(self, content: str) -> [bool, Account]:
        res, account = super(WeComInjector, self)._resolveMessage(content)
        return res, account
