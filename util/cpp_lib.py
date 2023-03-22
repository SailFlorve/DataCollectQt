import ctypes
import pathlib
from ctypes import c_int, string_at, windll, CFUNCTYPE, c_wchar_p
from typing import List

from util import log

DEFAULT_LIB = r".\lib\DataCollectUtil.dll"
DEFAULT_LIB_DEV = r"D:\Projects\VSProjects\DataCollectCpp\Debug\DataCollectUtil.dll"

'''
1. C++中的char* 需要.encode(utf-8)
2. C++中的wchar_t* 直接传
3. C++返回char* 需要设置restype  并decode utf-8 暂时不知道如何解码
4. C++返回wchar_t*  需要设置restype 直接拿返回值
'''


class CppLibrary:
    def __init__(self):
        """
        void inject(const wchar_t* processName, const wchar_t* dllPath, void(*callback)(BOOL, const wchar_t*));
        DWORD FindProcessId(const wchar_t* processName);
        int decryptBackup(const char* backupDir, const char* outputDir, int type, const char* bakKey);
        wchar_t* getUserPath();
        """
        self.dll = windll.LoadLibrary(DEFAULT_LIB)

    @staticmethod
    def decodeString(pStr, encoding="utf-8"):
        return string_at(pStr).decode(encoding)

    @staticmethod
    def encodeString(s: str, encoding="utf-8") -> bytes:
        return s.encode(encoding)

    @staticmethod
    def injectCallback(result: int, msg: str):
        log.i(result, msg)

    def getDocumentsPath(self):
        self.dll.getDocumentsPath.restype = c_wchar_p
        return self.dll.getDocumentsPath()

    def inject(self, processId: int, dllPath: str, callback):
        callbackDef = CFUNCTYPE(None, c_int, ctypes.c_wchar_p)
        self.dll.inject(processId, dllPath, callbackDef(callback))

    def findProcessId(self, processName: str) -> int:
        pid: int = self.dll.findProcessId(processName)
        return pid

    def findProcessIds(self, processName: str) -> [int, List]:
        function = self.dll.findProcessIds
        function.argtype = [ctypes.c_wchar_p, ctypes.POINTER(c_int)]
        function.res = ctypes.c_int
        pids = (ctypes.c_int * 5)()
        num = function(processName, pids)

        return num, [pids[i] for i in range(num)]

    def getProcessThreadCount(self, processName: str):
        f = self.dll.getProcessThreadCount
        f.argtype = [ctypes.c_wchar_p, ctypes.POINTER(c_int)]
        f.res = ctypes.c_int
        threadCounts = (ctypes.c_int * 5)()
        num = f(processName, threadCounts)
        return [threadCounts[i] for i in range(num)]

    def isPidHasWindowText(self, pid: int, text: str):
        result = self.dll.isPidHasWindowText(pid, text)
        return result

    def decryptWeChatBackupDb(self, backupDir: str, fileName: str, outputDir: str, bakKey: str, keyLen=0x20):
        # return // 0 成功 1 打开的文件不存在 2 key错误 3 写入文件出错
        return self.dll.decryptWeChatBackupDb(
            CppLibrary.encodeString(backupDir),
            CppLibrary.encodeString(fileName),
            CppLibrary.encodeString(outputDir),
            CppLibrary.encodeString(bakKey),
            keyLen
        )

    def decryptWeChatBackupFile(self, backupDir: str, fileName: str, outputDir: str, bakKey: str, keyLen=0x10):
        # 0 成功
        return self.dll.decryptWeChatBackupFile(
            CppLibrary.encodeString(backupDir),
            CppLibrary.encodeString(fileName),
            CppLibrary.encodeString(outputDir),
            CppLibrary.encodeString(bakKey),
            keyLen
        )

    def decryptQQDb(self, dllPath: str, dbPath: str, key: bytearray):
        key_bytes = (ctypes.c_ubyte * 16).from_buffer_copy(key)
        return self.dll.decryptQQDb(dllPath, CppLibrary.encodeString(dbPath), key_bytes)


if __name__ == '__main__':
    p = pathlib.Path("../main/lib/DataCollectUtil.dll")
    log.i(p.exists())
