import mimetypes
import os
import pathlib
import re
import subprocess
import sys
import time
import zipfile
from ctypes import windll

from PyQt5.QtCore import QFileInfo, QByteArray
from PyQt5.QtWidgets import QApplication, QWidget

from db.db_util import DBUtil
from util.cpp_lib import CppLibrary
from util.tools import Utility


def getCppLibDev():
    cl = CppLibrary()
    cl.dll = windll.LoadLibrary(r"D:\Projects\VSProjects\DataCollectCpp\Debug\DataCollectUtil.dll")
    return cl


def injectQQTest():
    cl = getCppLibDev()
    pid = cl.findProcessId("QQ.exe")
    cl.inject(pid, r"D:\Projects\VSProjects\DataCollectCpp\Debug\QQHookDLL.dll", cl.injectCallback)


def findProcessTest():
    cl = getCppLibDev()
    num, pids = cl.findProcessIds("QQ.exe")
    print(num)
    print(pids)


def isPidHasWindowTextTest():
    cl = getCppLibDev()
    print(cl.isPidHasWindowText(8224, "QQ"))


def openQQTest():
    cl = getCppLibDev()
    os.system(f"taskkill /F /IM QQ.exe")
    os.system(r'start "" C:\Users\Hang\Desktop\QQ\Bin\QQ.exe')

    d = {0: 0, 1: 0, 2: 0}
    lastNum = 0
    while True:
        num, pids = cl.findProcessIds("QQ.exe")
        if lastNum != num:
            d[lastNum] = 0

        lastNum = num
        d[num] += 1
        print(d)
        if num == 1 and d[num] > 10:
            print("可以注入")
        time.sleep(0.2)


def injectTargetQQ():
    cl = getCppLibDev()
    os.system(f"taskkill /F /IM QQ.exe")
    os.system(r'start "" C:\Users\Hang\Desktop\QQ\Bin\QQ.exe')
    while True:
        num, pids = cl.findProcessIds("QQ.exe")
        if num != 2:
            print(num, pids)
            time.sleep(0.5)
            continue
        else:
            print("num = 2", num, pids)
            thCnt = cl.getProcessThreadCount("QQ.exe")
            if thCnt.__len__() != 2 or thCnt[0] == thCnt[1]:
                print(thCnt)
                continue
            print(thCnt)
            index = thCnt.index(min(thCnt))
            print(index)
            cl.inject(pids[index], r"D:\Projects\VSProjects\DataCollectCpp\Release\QQHookDLL.dll",
                      cl.injectCallback)
            break


def getPathFromLink():
    fileInfo = QFileInfo(r'C:\Users\Hang\Desktop\QQ\QQ.lnk')

    return fileInfo.canonicalFilePath()


def hexTest():
    keyStr = "0x4D,0x70,0xB9,0x78,0x50,0xC1,0x20,0x1D,0x4A,0xBE,0x01,0xCC,0x38,0xAD,0xBE,0x92"
    keyStr = keyStr.replace("0x", "").replace(",", "")
    arr = bytearray.fromhex(keyStr)
    s = arr.fromhex(keyStr)
    print(arr)
    print(s)


def decryptQQTest():
    keyStr = "0xF8,0x9A,0x6C,0x97,0x26,0x53,0x19,0xA3,0x26,0x1E,0x48,0x74,0x7D,0xFC,0x3D,0x32"
    keyStr = keyStr.replace("0x", "").replace(",", "")
    arr = bytearray.fromhex(keyStr)
    cppLib = CppLibrary()
    cppLib.dll = windll.LoadLibrary(r"D:\Projects\VSProjects\DataCollectCpp\Release\DataCollectUtil.dll")
    decRes = cppLib.decryptQQDb(r"C:\Users\Hang\Desktop\QQ\Bin\KernelUtil.dll", r"D:/WeChatDecrypt/Msg3.0.db", arr)
    if decRes == 0:
        print("解密成功")
        f = open(r"D:/WeChatDecrypt/Msg3.0.db", mode="rb")
        f.seek(1024)
        fileBin = f.read()
        f.close()

        with open(r"D:/WeChatDecrypt/Msg3.0_dec.db", mode="wb+") as f1:
            f1.write(fileBin)

        while True:
            time.sleep(0.5)
            try:
                pathlib.Path("D:/WeChatDecrypt/Msg3.0.db").unlink(missing_ok=True)
            except OSError as e:
                print(e)


    else:
        print("解密失败", decRes)


def pathTest():
    path = pathlib.Path(
        r"D:\Documents\Tencent Files\1907464403\MsgBackup\70AF12E1909A0E64603D5FC3064067E4\7C4E9C310AF9E9B9B6D2F4A2509AB210")
    print(path.parent)
    print(path.parent.parent.name)


def timeTest():
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(1644997455)))


def hexToStr():
    b = bytearray([0x88, 0xf4, 0xcf, 0xd7])
    print(b.hex())


def getDocPath():
    cl = CppLibrary()
    print(cl.getDocumentsPath())


def _readFileAndWrite(filePath, offset, length, outputPath):
    with open(filePath, 'rb') as fr:
        fr.seek(offset, 0)
        content = fr.read(length)

        for i, l in enumerate(content.splitlines()):
            print(i, l)

        with open(outputPath, 'wb+') as fw:
            fw.write(content)


def unicodeDataTest():
    print(re.sub(r'[^a-zA-Z0-9_@]', '', "wxid_8rmcj0zs9itk22*8"))


def charInStrTest():
    l = range(48, 57)
    str = "ABCDE0"
    for idx, b in enumerate(str):
        print(b'\x30' == b)
        print(b'\x30')


def fileHeaderTest():
    headerD = {}
    headerSet = set()

    for f in pathlib.Path(r"D:\WeChatDecrypt\wxid_8rmcj0zs9itk22").rglob("*.bin"):
        fbytes = f.read_bytes()

        fbytes__hex = fbytes[0:8]
        if fbytes__hex in headerD:
            headerD[fbytes__hex] += 1
        else:
            headerD[fbytes__hex] = 1

    print(headerD)
    for k in headerD.keys():
        print(k, k.decode("utf-8", "ignore"))


def getAdminTest():
    print(subprocess.check_output(['icacls.exe', r"D:\1.txt", '/GRANT', 'administrators:F'], stderr=subprocess.STDOUT,
                                  encoding="gbk"))
    print(subprocess.check_output(
        ['cmd.exe', '/c', 'takeown', '/f', 'C:/Users/SailFlorve/Desktop/QQ 9.5.5.28014 NoQQProtect/Bin/QQ.exe'],
        stderr=subprocess.STDOUT,
        encoding="gbk"))


def injectWeCom():
    cl = CppLibrary()
    pid = cl.findProcessId("WXWork.exe")
    cl.inject(pid, r"D:\Projects\VSProjects\DataCollectCpp\Release\WeComHookDLL.dll", CppLibrary.injectCallback)


def decryptWeComDbTest():
    cl = CppLibrary()
    key = bytearray.fromhex("F2255359BA00544475776238A915875")
    print(cl.decryptWeChatBackupDb(r"D:\\", "message.db", "D:\\WeChatDecrypt", key.decode("utf-8")))


def readFileTest():
    Utility.readFileAndWrite(r"D:\WeChatDecrypt\wxid_8rmcj0zs9itk22\decrypt_BAK_0_MEDIA", 85286720, 13455024,
                             "D:\\test.mp4")


def setFileAttr():
    # reg.exe Add "HKLM\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "C:\Program Files\MyApp\Test.exe" /d "PUT__VALUE__HERE"
    import winreg
    import os
    # 添加注册表项
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                         r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
                         0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(key, r"D:\apps\Axure\AxureRP_9.0.0.3714_Green\Axure RP\Bin\AxureRP9.exe", 0, winreg.REG_SZ, "PUT__VALUE__HERE")
    winreg.CloseKey(key)


if __name__ == '__main__':
    setFileAttr()
