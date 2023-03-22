import math
import os
from pathlib import Path
from typing import List

from PyQt5.QtCore import QFileInfo

from account.account_ui import AccountWidget
from bean.beans import Account
from db.db_util import DBUtil
from util import log
from util.app_decrypter import AppDecrypter
from util.app_injector import AppInjector
from util.app_serializer import AppSerializer
from util.cpp_lib import CppLibrary
from util.tools import WinTool
from widget.custom_msgbox import CustomMsgBox


class AccountController:
    currentPage = 1
    dataType = -1

    def __init__(self, accountWidget: AccountWidget):
        self.accountWidget = accountWidget
        self.dataList: List[Account] = []  # 存储所有账号

        self.pageItemCount = 6
        self.cppLib = CppLibrary()

    def showMsgCallback(self, msgType: int, msg: str):
        self.accountWidget.showMsgSignal.emit(msgType, msg)

    def addAccount(self, uid=None):
        """
        添加账号，具体为：1.打开app 2.注入dll 3.回调注入结果 4.监听DLL发送的消息
        :param uid: uid不为None，则为更新激活状态
        """

        # 子线程
        def injectCallback(res, msg):
            """
            :param msg:
            :param res: 0 - 成功
            """
            if res != 0:
                self.showMsgCallback(0, msg)
                self.accountWidget.enableAddAccountSignal.emit()
            else:
                log.w(res, msg)
                injector.receiveMessage()

        # 子线程
        def messageReceiveListener(success: bool, typ, account: Account):

            self.accountWidget.setAddAccountBtnEnabled(True)

            if not success:
                return

            if uid is not None and account.uid != uid:
                self.showMsgCallback(0, "登录的账号与需要激活的账号不一致。")
                return

            dbUtil = DBUtil(autoClose=False)

            if uid is not None:
                # 更新激活状态
                dbUtil.exec(DBUtil.SQL_ACTIVE_ACCOUNT, account.active, account.keyDb, account.keyBak,
                            account.path, account.profile, account.time, account.uid)
            else:
                # 查询是否存在
                _, accountRes = dbUtil.exec(DBUtil.SQL_QUERY_ACCOUNT_BY_ID, account.uid)
                if len(accountRes) != 0:
                    # 存在则删除
                    dbUtil.exec(DBUtil.SQL_DELETE_ACCOUNT, account.uid)
                dbUtil.exec(DBUtil.SQL_ADD_ACCOUNT, account.uid, account.keyDb, account.keyBak,
                            account.time, typ, account.path, account.profile, True)

            # 更新数据
            self.accountWidget.addAccountSignal.emit(typ)

            dbUtil.close()

        def onAppExit():
            self.accountWidget.enableAddAccountSignal.emit()

        def onGetAppInstallPath(typ, path: str):
            path = path.replace(r'"', "")
            log.d(path)

            p = Path(path)
            if p.suffix == ".lnk":
                p = Path(QFileInfo(path).canonicalFilePath())

            parentPath = str(p.parent.resolve())
            log.d(parentPath)
            dbUtil = DBUtil(autoClose=False)
            dbUtil.exec(DBUtil.SQL_DELETE_APP_INSTALL_PATH, typ)
            dbUtil.exec(DBUtil.SQL_ADD_APP_INSTALL_PATH, typ, parentPath)
            dbUtil.close()

        self.accountWidget.setAddAccountBtnEnabled(False)
        injector = AppInjector.getInjector(self.dataType)
        injector.showMsgCallback = self.showMsgCallback
        injector.onGetAppInstallPathCallback = onGetAppInstallPath
        injector.inject(injectCallback, messageReceiveListener, onAppExit)

    # 获取分页账号列表
    def getData(self, page: int, typ):
        allPage = math.ceil(len(self.dataList) / self.pageItemCount)

        if len(self.dataList) != 0 and (page < 1 or page > allPage):
            return

        if len(self.dataList) == 0:
            page = 1

        self.currentPage = page

        if self.dataType != typ:
            self.dataType = typ
            self.__getDataInternal(typ)

            allPage = math.ceil(len(self.dataList) / self.pageItemCount)

        self.accountWidget.refreshList(
            self.dataList[self.pageItemCount * (page - 1):self.pageItemCount * page], page, allPage)

    # 刷新账号列表，并显示为第1页
    def refreshData(self):
        typ = self.dataType
        self.dataType = -1
        self.getData(1, typ)

    def __getDataInternal(self, accType: int):
        self.dataType = accType
        self.dataList.clear()

        self.dataList = self.__getAccountFromDb()

    def __getAccountFromDb(self) -> List[Account]:
        dbUtil = DBUtil()
        execRes, execData = dbUtil.exec(DBUtil.SQL_QUERY_ACCOUNT_BY_TYPE, self.dataType, dictResult=True)
        accountList = []

        for accountData in execData:
            account = Account(
                accountData['uid'],
                accountData['profile'],
                accountData['type'],
                accountData['active'],
                accountData['key_db'],
                accountData['key_bak'],
                accountData['time'],
                accountData['path']
            )
            accountList.append(account)

        return accountList

    def getLastPage(self, typ):
        self.dataType = -1
        lastPage = math.ceil(len(self.dataList) / self.pageItemCount)
        lastPage = 1 if lastPage == 0 else lastPage
        self.getData(lastPage, typ)

    def active(self, active: bool, i, account: Account):
        """
        :param account:
        :param i:
        :param active: 指的是想要的行为，如当前为激活则想要反激活，active为False
        """
        dbUtil = DBUtil()

        # 反激活, 啥也不做
        if not active:
            return

        # 激活，走登录流程，但是检测登录的账号是否与account.uid一致
        else:
            if self.accountWidget.btnAddAccount.isEnabled():
                self.addAccount(account.uid)

    # 解密+序列化，解密成功回调内部会进行序列化
    def decrypt_and_serialize(self, i, account: Account):

        dbUtil = DBUtil(autoClose=False)

        def serializeCallback(isFinished, msg):
            self.accountWidget.showMsgSignal.emit(0 if isFinished else 2, msg)

        # 主线程
        def decryptCallback(statusList: List):  # [dbStatus, dbMsg, backupStatus, backupMsg]
            if len(statusList) != 4:
                CustomMsgBox.showMsg("激活失败。", CustomMsgBox.ICON_QUESTION)
                return
            dbStatus = statusList[0]
            dbMsg = statusList[1]
            bakStatus = statusList[2]
            bakMsg = statusList[3]

            message = f"数据库: {dbMsg}\n备份数据: {bakMsg}\n"

            """
                  备份数据  成功        失败
            数据库         
            成功         进行序列化    提示没有备份
            失败         取消激活      取消激活
            """
            errorOccurred = not (dbStatus and bakStatus)
            if not dbStatus:
                message += "\n已取消激活，请点击激活按钮重新激活！"
                self.accountWidget.onActive(False, False, i)
                dbUtil.exec(DBUtil.SQL_ACTIVE_ACCOUNT, False, "123", account.keyBak,
                            account.path, account.profile, account.time, account.uid)

                CustomMsgBox.showMsg(message, CustomMsgBox.ICON_QUESTION if errorOccurred else CustomMsgBox.ICON_OK)
            else:
                if bakStatus:
                    log.i(message)
                    ae = AppSerializer.getInstance(account)
                    ae.serialize(serializeCallback, self.accountWidget)
                else:
                    CustomMsgBox.showMsg(message, CustomMsgBox.ICON_QUESTION if errorOccurred else CustomMsgBox.ICON_OK)

            dbUtil.close()

        if not account.active:
            CustomMsgBox.showToast("还未激活，请先激活。", CustomMsgBox.ICON_QUESTION)
        else:
            CustomMsgBox.showStatus("正在解密...")
            outputPath = self.__getOutputPath(account, dbUtil)

            # decryptCallback([True, "", True, ""])
            AppDecrypter.decrypt(account, outputPath, decryptCallback, self.accountWidget, self.showMsgCallback)

    @staticmethod
    def __getOutputPath(account, dbUtil):
        _, settings = dbUtil.exec(DBUtil.SQL_QUERY_SETTINGS)
        if settings[account.type][1] == "":
            outputPath = settings[3][1]
        else:
            outputPath = settings[account.type][1]
        outputPath = os.path.expandvars(outputPath)
        return outputPath

    def openDecryptedDir(self, account: Account):
        dbUtil = DBUtil()
        outputPath = self.__getOutputPath(account, dbUtil)
        outputPath = os.path.join(outputPath, account.uid)

        if os.path.exists(outputPath):
            WinTool.openDir(outputPath)
        else:
            CustomMsgBox.showMsg("文件夹不存在，请先解密。", CustomMsgBox.ICON_QUESTION)
