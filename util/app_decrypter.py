"""
将数据库复制到输出目录、使用Key对数据库进行解密。
"""

import os.path
import pathlib
import shutil
from typing import List, Callable, Dict

from PyQt5.QtCore import QObject, QThread

from bean.beans import Account, SocialConfig
from db.db_util import DBUtil
from util import log
from util.cpp_lib import CppLibrary


class AppDecrypter(QObject):
    @staticmethod
    def decrypt(account: Account, outputDir: str,
                callback: Callable[[List], None], parent: QObject,
                showMsgCallback):
        decryptThread = DecryptThread(account, outputDir, parent=parent, showMsgCallback=showMsgCallback)
        decryptThread.start()
        decryptThread.finished.connect(lambda: callback(decryptThread.decryptResult))


class DecryptThread(QThread):
    def __init__(self, account: Account, outputDir: str, parent=None, showMsgCallback=None):
        super(DecryptThread, self).__init__(parent=parent)
        self.account = account

        self.decryptResult = []
        self.appType = self.account.type
        self.dbStatus = True
        self.backupStatus = True
        self.dbMsg = "数据库解密成功"
        self.backupMsg = "备份数据解密成功"
        self.cppLib = CppLibrary()

        self.showMsgCallback = showMsgCallback

        self.outputDirPath = pathlib.Path(outputDir) / self.account.uid

        # 确保输出目录是空的
        shutil.rmtree(self.outputDirPath, ignore_errors=True)
        self.outputDirPath.mkdir(parents=True, exist_ok=True)

    def run(self):
        import pydevd
        try:
            pydevd.settrace(suspend=False)
        except ConnectionRefusedError:
            pass

        runDict = {
            SocialConfig.WECHAT: self.decryptWechat,
            SocialConfig.QQ: self.decryptQQ,
            SocialConfig.WECOM: self.decryptWeCom
        }
        runDict[self.appType]()

    def decryptWechat(self):
        dbDirPath = pathlib.Path(f"{self.account.path}") / "decrypt_temp" / self.account.uid
        if dbDirPath.exists():
            shutil.copytree(dbDirPath, self.outputDirPath, dirs_exist_ok=True)
            self.dbMsg = "数据库解密成功"
        else:  # 没有数据库文件, 引导重新登录。
            log.i(f"解密数据库文件失败, {dbDirPath}")
            self.dbMsg = "解密数据库文件失败"
            self.dbStatus = False

        if self.dbStatus:
            backupRootPath = pathlib.Path(f"{self.account.path}\\{self.account.uid}\\BackupFiles")
            if len(os.listdir(backupRootPath)) == 0:
                self.backupMsg = "没有备份文件"
                self.backupStatus = False
            else:
                backupPath = backupRootPath / os.listdir(backupRootPath)[0]
                for filePath in backupPath.glob("*"):
                    self.showMsgCallback(2, f"正在解密{filePath.name}...")
                    if filePath.name == "Backup.db":
                        result = self.cppLib.decryptWeChatBackupDb(str(backupPath),
                                                                   filePath.name,
                                                                   str(self.outputDirPath),
                                                                   self.account.keyBak)
                        if result != 0:
                            self.backupStatus = False
                            self.backupMsg = f"解密{filePath.name}错误, {result} [1: 打开的文件不存在 2:key错误 3: 写入文件出错]"
                            break

                    elif "MEDIA" in filePath.name or "TEXT" in filePath.name:
                        result = self.cppLib.decryptWeChatBackupFile(str(backupPath),
                                                                     filePath.name,
                                                                     str(self.outputDirPath),
                                                                     self.account.keyBak)
                        if result != 0:
                            self.backupStatus = False
                            self.backupMsg = f"解密{filePath.name}错误：{result}"
                            break

        self.generateResult()

    def decryptQQ(self):
        dbUtil = DBUtil()
        appInstallRes = dbUtil.exec(DBUtil.SQL_GET_APP_INSTALL_PATH, self.appType, needResult=False, dictResult=True)
        appPath = appInstallRes[0]['path']
        dbKeyDict: Dict[str, str] = {}
        # keyBak是："数据库路径&key#数据库路径&key#数据库路径&key"
        dbKeyPairList = self.account.keyBak.split("#")

        for dbKeyPairStr in dbKeyPairList:
            if len(dbKeyPairStr) == 0:
                continue
            dbKeyPair = dbKeyPairStr.split("&")
            dbKeyDict[dbKeyPair[0]] = dbKeyPair[1]

        for dbPathStr, dbKey in dbKeyDict.items():
            dbPath = pathlib.Path(dbPathStr)
            dbName = dbPath.name
            self.showMsgCallback(2, f"正在解密{dbName}")
            if dbPath.parent.parent.name == "MsgBackup":
                backupDstPath = self.outputDirPath / "MsgBackup"
                backupDstPath.mkdir(parents=True, exist_ok=True)
                dstPath = backupDstPath / dbName
            else:
                dstPath = self.outputDirPath / dbName
            # 先复制到输出文件夹
            shutil.copyfile(dbPathStr, dstPath)

            keyStr = dbKey.replace("0x", "").replace(",", "")
            keyArr = bytearray.fromhex(keyStr)

            # 调用C++， 使用sqlite3_rekey解密源文件
            decRes = self.cppLib.decryptQQDb(str(pathlib.Path(appPath) / "KernelUtil.dll"), str(dstPath), keyArr)

            if decRes == 0:
                # 从第1024字节读取文件
                with open(dstPath, mode="rb") as dbWithEmptyHeader:
                    dbWithEmptyHeader.seek(1024)
                    fileBin = dbWithEmptyHeader.read()

                # 写入新文件
                with open(dstPath.parent / ("decrypt_" + dbName + ".db"), mode="wb+") as dbDecrypted:
                    dbDecrypted.write(fileBin)

                # 删除原来带空头的文件
                pathlib.Path(dstPath).unlink(missing_ok=True)

            else:
                self.dbStatus = False
                self.dbMsg = f"数据库{dbName}解密失败，错误码{decRes}。[21: 程序错误。26: Key错误。]"
                break

        self.backupStatus = True
        self.backupMsg = "备份数据库解密成功"

        self.generateResult()

    def decryptWeCom(self):
        dbDirPath = pathlib.Path(f"{self.account.path}") / "decrypt_temp" / self.account.uid
        if dbDirPath.exists() and len(os.listdir(dbDirPath)) > 5:
            shutil.copytree(dbDirPath, self.outputDirPath, dirs_exist_ok=True)
            self.dbMsg = "数据库解密成功"
        else:
            log.i(f"解密数据库文件失败, {dbDirPath}")
            self.dbMsg = "解密数据库文件失败。"
            self.dbStatus = False
        self.backupStatus = True
        self.backupMsg = "无需解密。"
        self.generateResult()

    def generateResult(self):
        self.decryptResult.extend([self.dbStatus, self.dbMsg, self.backupStatus, self.backupMsg])
