"""
针对已经解密的文件，进行序列化；复制用户目录下的非加密资源或解密加密资源
"""

import os.path
import pathlib
import shutil
from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Callable, Union, Dict

import unicodedata
from PyQt5.QtCore import QObject, QThread

from bean.beans import Account, SocialConfig
from db.db_util import DBUtil
from util import log
from util.tools import Utility


# noinspection SqlDialectInspection
class AppSerializer(QObject):
    def __init__(self, account: Account):
        """
        将聊天记录转化为Json并提取聊天文件。
        :param account:
        """
        super(AppSerializer, self).__init__()
        self.account = account

        self.callback: Callable[[bool, str], None] = Callable[[bool, str], None]  # bool 是否结束 str msg
        self.outputDir: pathlib.Path = pathlib.Path()  # 解密路径 + 用户ID

    @staticmethod
    def getInstance(account: Account):
        if account.type == SocialConfig.WECHAT:
            return WechatSerializer(account)
        elif account.type == SocialConfig.QQ:
            return QQSerializer(account)
        elif account.type == SocialConfig.WECOM:
            return WeComSerializer(account)

    def serialize(self, callback: Callable[[bool, str], None], parent: QObject):
        """
        1. 查询数据库
        2. 查找BAK_0_TEXT，序列化为JSON
        3. 提取BAK_0_MEDIA
        4. 复制fileStorage并解密
        """
        thread = QThread(parent)
        thread.run = lambda: self.__serializeInternal(callback)
        thread.start()

    def __serializeInternal(self, callback):

        import pydevd
        try:
            pydevd.settrace(suspend=False)
        except ConnectionRefusedError as e:
            print(e)

        self.callback = callback

        executeList = [self._getOutputPath,
                       self.readDatabase,
                       self.outputJson,
                       self.extractMedia,
                       self.copyUserDir]

        promptList = [None, "正在读取数据库...", "正在将聊天记录转换成Json...", "正在提取媒体文件...", "正在复制用户文件夹..."]

        for i, execute in enumerate(executeList):
            if promptList[i] is not None:
                self.callback(False, promptList[i])
            try:
                if not execute():
                    return
            except FileNotFoundError as e:
                self.callback(True, f"{promptList[i]}发生错误: \n{e}")
                return

        self.callback(True, "全部数据已经解密及序列化成功。")

    def _getOutputPath(self) -> bool:
        du = DBUtil()
        res, settings = du.exec(DBUtil.SQL_QUERY_SETTINGS, needResult=True, dictResult=True)
        if not res:
            self.callback(True, "数据库文件损坏。")
            return False

        outputDir = settings[self.account.type]["path"]
        if len(outputDir) == 0:
            outputDir = os.path.expandvars(settings[3]["path"])

        outputDir = pathlib.Path(outputDir) / self.account.uid
        self.outputDir = outputDir
        return True

    @abstractmethod
    def readDatabase(self) -> bool:
        """
        读取相关数据库，获取相关信息
        """
        pass

    @abstractmethod
    def outputJson(self) -> bool:
        """
        把聊天记录转换成Json
        """
        pass

    @abstractmethod
    def extractMedia(self) -> bool:
        """
        从数据库中提取媒体文件
        """
        pass

    @abstractmethod
    def copyUserDir(self) -> bool:
        """
        解密dat文件
        """
        pass

    @staticmethod
    def __getFormat(code: int) -> int:
        """
        :rtype: 0 0xxxxxxx 1 10xxxxxx 2 110xxxxx 3 1110xxxx 4 11110xxx -1 not
        """
        if 0 <= code <= 127:
            return 0
        if 128 <= code <= 191:
            return 1
        if 192 <= code <= 223:
            return 2
        if 224 <= code <= 239:
            return 3
        if 239 <= code <= 247:
            return 4
        return -1

    def _decodeUtf8(self, line: bytes) -> str:
        """
        将bytes出去所有非UTF-8字符，转换成str
        """
        result = line.decode("utf-8", 'ignore')
        result = "".join(ch for ch in result if unicodedata.category(ch)[0] != "C")
        return result

        # result = bytearray()
        # index = -1
        # while index < len(line) - 1:
        #     index += 1
        #     byte = line[index]
        #     if byte <= 31:
        #         continue
        #     form = self.__getFormat(byte)
        #
        #     if form == 1 or form == -1:
        #         continue
        #     if form == 0:
        #         result.append(byte)
        #         continue
        #
        #     byteArrTmp = bytearray()
        #     # 取index后的form - 1个数字
        #     if index + form - 1 >= len(line):  # 越界
        #         continue
        #     byteArrTmp.append(byte)
        #     for j in range(form - 1):
        #         byteAfter = line[index + j + 1]
        #         if self.__getFormat(byteAfter) == 1:
        #             byteArrTmp.append(byteAfter)
        #         else:
        #             byteArrTmp.clear()
        #             break
        #     if len(byteArrTmp) == 0:
        #         continue
        #     else:
        #         index += form - 1 if form >= 2 else 0
        #         try:
        #             byteArrTmp.decode("utf-8")
        #             result.extend(byteArrTmp)
        #         except UnicodeDecodeError:
        #             pass
        # text = result.decode("utf-8")
        # return text

# 用于ORM

@dataclass
class WeChatSession:
    id: int
    talker: str
    nickName: str
    startTime: int
    endTime: int


@dataclass
class WeChatMedia:
    mediaId: int
    offset: int
    length: int
    mediaIdStr: str
    fileName: str
    talkerId: str


@dataclass
class WeChatMsgSegment:
    takerId: int
    startTime: str
    endTime: str
    offset: int
    length: int
    weChatId: str
    fileName: str


weChatIdRangeList = list(range(97, 123))
weChatIdRangeList.extend(list(range(65, 91)))
weChatIdRangeList.extend(list(range(48, 58)))
weChatIdRangeList.extend([64, 95])


# noinspection SqlDialectInspection
class WechatSerializer(AppSerializer):
    def __init__(self, account):
        super(WechatSerializer, self).__init__(account)
        self.sessionDict: Dict[int, WeChatSession] = {}  # {key: talkerId value:Session}
        self.mediaDict: Dict[int, WeChatMedia] = {}  # {key: talkerId, value: Media}
        self.msgSegmentList: List[WeChatMsgSegment] = []
        # self.typeListFiltered = []  # 0 ID 1 普通消息 2 数据库字段
        # self.textListFiltered = []

        self.chatMsgList = ()  # placeholder

    def _parseChatText(self, textSegment: bytes) -> List:
        idNum = 0
        textList: List[List[int, str]] = []  # -1 被过滤了 0 ID 1 普通消息 2 数据库

        for i, line in enumerate(textSegment.splitlines()):
            if i == 0:
                continue
            text = self._decodeUtf8(line)

            # 跳过长度为0
            if len(text) <= 1:
                continue

            # 1. 长度大于25，认为是消息
            # 2. 上个是ID，当前一定是ID
            # 3. 连续出现两个ID，下一个一定不是ID
            # 4. 长度小于25，且不包含<，且最后一个字符是控制符, 认为是ID; 但text长度小于6，不是ID。
            if len(line) > 24:
                # log.d("A")
                idNum = 0
                msgType = 1
            elif idNum == 1:
                # log.d("B")
                idNum += 1
                msgType = 0
            elif idNum == 2:
                # log.d("E")
                idNum = 0
                msgType = 1
            elif len(line) <= 24 and line[-1] <= 31 and "<" not in text:
                if len(text) < 6:
                    continue
                else:
                    # log.d("C")
                    idNum += 1
                    msgType = 0
            else:
                # log.d("D")
                idNum = 0
                msgType = 1
            textTuple = [msgType, text]
            self._filterText(textTuple)
            textList.append(textTuple)
        return textList

    # noinspection SqlResolve
    def readDatabase(self) -> bool:
        backupDbPath = self.outputDir / "decrypt_Backup.db"
        log.d(self.outputDir, backupDbPath)
        if not backupDbPath.exists():
            self.callback(True, f"在{str(backupDbPath)}中没有找到解密后的Backup.db。")
            return False

        backupDbUtil = DBUtil(str(backupDbPath), False)
        res, sessions = backupDbUtil.exec("select talker, NickName, StartTime, EndTime from Session")
        if not res:
            self.callback(True, "查询Backup.db中的Session失败。")

        for i, session in enumerate(sessions):
            self.sessionDict[i + 1] = WeChatSession(i + 1, session[0], session[1], session[2], session[3])

        res, medias = backupDbUtil.exec("select MsgMedia.MediaId, MsgMedia.MediaIdStr, "
                                        "MsgFileSegment.Offset, MsgFileSegment.TotalLen, MsgFileSegment.FileName, "
                                        "MsgMedia.talker "
                                        "from MsgMedia join MsgFileSegment "
                                        "on MsgMedia.MediaId = MsgFileSegment.MapKey "
                                        "where MsgFileSegment.InnerOffSet = 0")

        if not res:
            self.callback(True, "查询Backup.db中的MsgMedia join MsgFileSegment失败。")
        for media in medias:
            self.mediaDict[media[1]] = WeChatMedia(media[0], media[2], media[3], media[1], media[4], media[5])

        res, msgSegments = backupDbUtil.exec("select talkerId, StartTime, EndTime, OffSet, Length, UsrName, FilePath "
                                             "from MsgSegments")
        if not res:
            self.callback(True, "查询Backup.db中的MsgSegments失败。")

        for msgSegment in msgSegments:
            self.msgSegmentList.append(WeChatMsgSegment(msgSegment[0], msgSegment[1], msgSegment[2], msgSegment[3],
                                                        msgSegment[4], msgSegment[5], msgSegment[6]))

        backupDbUtil.close()
        return True

    # def outputJsonDeprecated(self) -> bool:
    #     bakText = self.outputDir / "decrypt_BAK_0_TEXT"
    #     if not bakText.exists():
    #         self.callback(True, f"没有在{str(self.outputDir)}下找到decrypt_BAK_0_TEXT")
    #         return False
    #
    #     self._parseChatText(bakText)
    #
    #     jsonStr = self._generateMsgSegmentJsonDict()
    #
    #     jsonOutputDir = self.outputDir / "decrypt_BAK_0_TEXT_JSON.json"
    #     jsonOutputDir.write_text(jsonStr, encoding="utf-8")
    #     return True

    def outputJson(self) -> bool:
        msgSegmentLen = len(self.msgSegmentList)

        # 总Dict
        msgTextJsonObjListDict: Dict[int, List] = {}  # {talkerId: jsonObj}

        segmentNum = 0

        for i, msgSegment in enumerate(self.msgSegmentList):
            self.callback(False, f"正在解析聊天记录...{i / msgSegmentLen * 100:.2f}%")

            if msgSegment.takerId not in msgTextJsonObjListDict:
                segmentNum = 0
                sessionInfo = self.sessionDict[msgSegment.takerId]
                msgTextJsonObjListDict[msgSegment.takerId] = [{
                    "WeChatId": sessionInfo.talker,
                    "NickName": sessionInfo.nickName,
                    "StartTime": Utility.getFormatTime(sessionInfo.startTime / 1000),
                    "EndTime": Utility.getFormatTime(sessionInfo.endTime / 1000)
                }]

            segmentNum += 1

            bakTextPath = self.outputDir / f"decrypt_{msgSegment.fileName}"
            if not bakTextPath.exists():
                self.callback(True, f"没有在{str(self.outputDir)}下找到decrypt_{msgSegment.fileName}")
                return False

            msgSegBytes = Utility.readFile(bakTextPath, msgSegment.offset, msgSegment.length)
            msgList = self._parseChatText(msgSegBytes)
            jsonObj = self._generateMsgSegmentJsonDict(segmentNum, msgSegment, msgList)
            msgTextJsonObjListDict[msgSegment.takerId].append(jsonObj)

        for index, talkerId in enumerate(msgTextJsonObjListDict):
            talker = self.sessionDict[talkerId].talker
            self.callback(False,
                          f"正在输出{talker}聊天记录...{index}/{len(msgTextJsonObjListDict)}")

            jsonObj = msgTextJsonObjListDict[talkerId]
            jsonOutputDir = self.outputDir / f"{talker}.json"
            jsonStr = Utility.getJsonStr(jsonObj)
            jsonOutputDir.write_text(jsonStr, encoding="utf-8", errors="ignore")

        return True

    # noinspection SpellCheckingInspection
    def __getMsgType(self, msg: str) -> [int, str]:
        """
        :return 0 普通 1语音 2图片 3视频 4文件 + 文件后缀(文件类型为文件名字)
        """
        if msg.find(r"<msg><voicemsg") != -1:
            return 1, ".slk"
        if msg.find(r"<msg><img") != -1:
            return 2, ".jpg"
        if msg.find(r"<msg><videomsg") != -1:
            return 3, ".mp4"
        if msg.find(r"<msg><appmsg") != -1:
            fileName = Utility.findTabInXml(msg, "title")
            return 4, fileName

    # def extractMediaDeprecated(self) -> bool:
    #     lastMsg = ""
    #     filePath = self.outputDir / "decrypt_BAK_0_MEDIA"
    #
    #     # 这个文件可能不存在
    #     if not filePath.exists():
    #         return True
    #
    #     for i, value in enumerate(self.typeListFiltered):
    #         if value == 1:
    #             lastMsg = self.textListFiltered[i]
    #         elif value == 2:
    #             msgType, fileExt = self.__getMsgType(lastMsg)
    #             mediaIdStr = self.textListFiltered[i]
    #             if mediaIdStr not in self.mediaDict:
    #                 continue
    #             media = self.mediaDict[mediaIdStr]
    #             outputFile = mediaIdStr + fileExt
    #             outputFileDir = self.outputDir / "BAK_0_MEDIA_EXTRACT"
    #             outputFileDir.mkdir(exist_ok=True)
    #             outputFilePath = outputFileDir / outputFile
    #             Utility.readFileAndWrite(str(filePath), media.offset, media.length, str(outputFilePath))
    #     return True

    def extractMedia(self) -> bool:
        index = 0
        for mediaIdStr, media in self.mediaDict.items():
            index += 1
            if index % 12 == 0:
                self.callback(False, f"正在提取文件...{index}/{len(self.mediaDict)}")
            filePath = self.outputDir / f"decrypt_{media.fileName}"
            fileBytes = Utility.readFile(filePath, media.offset, media.length)
            outputFilePath = self.outputDir / media.talkerId
            outputFilePath.mkdir(parents=True, exist_ok=True)
            Utility.writeFile(outputFilePath / media.mediaIdStr, fileBytes, True)
        return True

    def copyUserDir(self) -> bool:
        dirPicked = ["Cache", "File", "Image", "Video"]
        srcFileStoragePath = pathlib.Path(self.account.path) / self.account.uid / "FileStorage"
        dstFileStoragePath = self.outputDir / "FileStorage"

        if not srcFileStoragePath.exists():
            return True

        # 复制文件到输出目录
        for dirName in dirPicked:
            dirPath = srcFileStoragePath / dirName
            dstPath = dstFileStoragePath / dirName
            dstPath.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dirPath, dstPath, dirs_exist_ok=True)

        # 解密image文件夹
        imagePath = dstFileStoragePath / "Image"
        if not imagePath.exists():
            return True

        for filePath in imagePath.glob("**/*.dat"):
            fileName = filePath.stem + ".jpg"
            self.callback(False, f"正在解密{filePath.name}")
            key = 0
            fr = open(filePath, "rb")
            fw = open(imagePath / fileName, 'wb+')
            newFileBytes = bytearray()
            for line in fr:
                for b in line:
                    if key == 0:
                        key = b ^ 0xff
                    newFileBytes.append(b ^ key)
            fw.write(newFileBytes)
            fr.close()
            fw.close()
        return True

    @staticmethod
    def __filterId(idStr: str):
        # id范围 0-9 a-z A-Z _ @ 且匹配连续的字符
        # return re.sub(r'[^a-zA-Z0-9_@]\w+', '', idStr)

        nonMatchIdx = 0

        for idx, b in enumerate(idStr):
            if ord(b) in weChatIdRangeList:
                continue
            else:
                nonMatchIdx = idx
                break

        return idStr[0:nonMatchIdx]

    @staticmethod
    def __filterMsg(msgStr: str):
        # 消息从最后一个08截断
        index = msgStr.rfind("08")
        if index == -1:
            index = len(msgStr)
        return msgStr[0:index]

    def __isMediaId(self, msgStr: str) -> Union[bool, str]:
        index = msgStr.rfind("_backup")
        if index == -1:
            return False

        mediaId = msgStr[1:index + 7]
        res = mediaId in self.mediaDict

        if res is False:
            return res
        else:
            if "__thumb" in msgStr:
                mediaId += "__thumb"
            return mediaId

    def _filterText(self, typeTextTuple):
        textType = typeTextTuple[0]
        text = typeTextTuple[1]

        if textType == 0:  # 微信id
            # 长度小于6不可能是id
            if len(text) < 6:
                typeTextTuple[0] = -1
                return
            typeTextTuple[1] = self.__filterId(text)
        else:
            result = self.__isMediaId(text)
            if not result:
                typeTextTuple[1] = self.__filterMsg(text)
            else:
                typeTextTuple[0] = 2

    def _generateMsgSegmentJsonDict(self, index, msgSegment: WeChatMsgSegment, textList: List) -> Dict:

        msgSegmentDict = {}
        lastType = 0

        chatIdList = []
        chatMsg = ""
        chatLen = len(textList)

        msgSegmentDict["Segment"] = index
        msgSegmentDict["StartTime"] = Utility.getFormatTime(float(msgSegment.startTime) / 1000)
        msgSegmentDict["EndTime"] = Utility.getFormatTime(float(msgSegment.endTime) / 1000)

        msgList = []

        for i in range(chatLen):
            typ = textList[i][0]
            txt = textList[i][1]

            if typ == -1:
                continue

            if i == chatLen - 1:
                chatMsg += txt

            # 从消息变为微信ID或者到达最后一条，且有两个人，存储消息
            if lastType >= 1 and typ == 0 or i == chatLen - 1:
                if len(chatIdList) != 2:
                    log.e(f"在消息\n{chatIdList}\n{chatMsg}\n处发生错误，因为对话人数不为2。")
                    for _ in range(len(chatIdList), 2):
                        chatIdList.append("unknown_wechat_id")

                newDict = {
                    "Sender": chatIdList[0],
                    "Msg": chatMsg
                }

                # 查看session字典是否存在，不存在创建，存在创建新字典

                # talkerId = msgSegment.takerId
                # startTimeUnix = float(self.sessionDict[talkerId].startTime)
                # endTimeUnix = float(self.sessionDict[talkerId].endTime)
                # startTimeFormat = Utility.getFormatTime(startTimeUnix / 1000)
                # endTimeFormat = Utility.getFormatTime(endTimeUnix / 1000)
                # newSessionDict = {
                #     "TalkerId": talkerId,
                #     "Nickname": self.sessionDict[talkerId].nickName,
                #     "StartTime": startTimeFormat,
                #     "EndTime": endTimeFormat,
                #     "Content": [newDict]
                # }
                msgList.append(newDict)

                chatIdList.clear()
                chatMsg = ""

            lastType = typ
            if typ == 0:
                chatIdList.append(txt)
            else:
                chatMsg += txt
                chatMsg += "\n"

        msgSegmentDict["Messages"] = msgList

        return msgSegmentDict


@dataclass
class QQChat:
    id: str
    msgData: bytes
    msgSeq: str
    chatUin: str
    msgTime: str
    dbFileResId: List[str]


# noinspection SqlDialectInspection,SpellCheckingInspection,SqlResolve
class QQSerializer(AppSerializer):
    TABLE_MSG = 0
    TABLE_RES = 1
    TABLE_RES_FILE = 2
    TABLE_FILE_CONTEXT = 3

    BAK_DIR = "MsgBackup"

    def __init__(self, account: Account):
        super(QQSerializer, self).__init__(account)
        self.resDbUtil: List[DBUtil] = []

        self.idMsgDict: Dict[str, List[QQChat]] = {}  # {id : [""]}
        self.idResDict: Dict[str, Dict[str, List[str]]] = {}  # {id: {msgSeq: [resInfoId]}}
        self.fileContextDict: Dict[str, str] = {}  # {resId: dbFileResId}

    def readDatabase(self) -> bool:
        """
        读取msg_n_id时，存储到idMsgDict；读取res_n_id时，存储到idResDict；读取到fileContextDict时，存储到fileContextDict
        读取到resfile时，将该数据库存储到resDbUtil
        """
        backupPath = self.outputDir / self.BAK_DIR
        for backupDb in backupPath.glob("*"):
            dbUtil = DBUtil(str(backupDb), autoClose=False)
            tableRes = dbUtil.exec("select name from sqlite_master where type = 'table'", needResult=False)

            for tableList in tableRes:
                tableName = tableList[0]
                dbType = self.__getDatabaseType(tableName)
                if dbType == self.TABLE_RES_FILE:
                    self.resDbUtil.append(dbUtil)
                    break
                else:
                    self.callback(False, f"正在读取{tableName}")
                    self.__readDatabaseInternal(dbUtil, dbType, tableName)

        for qqId, QQChatList in self.idMsgDict.items():
            msgSeqDict = self.idResDict[qqId]

            for qqChat in QQChatList:
                if qqChat.msgSeq not in msgSeqDict:
                    continue
                else:
                    resInfoIdList = msgSeqDict[qqChat.msgSeq]
                    for resInfoId in resInfoIdList:
                        qqChat.dbFileResId.append(self.fileContextDict[resInfoId])

        return True

    def outputJson(self) -> bool:
        """
        把聊天记录转换成Json（按QQ号）
        """
        for qqId, qqChatList in self.idMsgDict.items():
            idBakPath = self.outputDir / self.BAK_DIR
            idBakPath.mkdir(parents=True, exist_ok=True)

            jsonObj = []
            for qqChat in qqChatList:
                chatMsgDict = {"time": Utility.getFormatTime(float(qqChat.msgTime)),
                               "msg": self._decodeUtf8(
                                   qqChat.msgData[qqChat.msgData.rfind(0x0a) + 2:qqChat.msgData.rfind(0x4a)]),
                               "sender": qqChat.msgData[3:8].hex(),
                               "receiver": qqChat.msgData[9:14].hex()}

                if len(qqChat.dbFileResId) != 0:
                    chatMsgDict["resource"] = qqChat.dbFileResId
                jsonObj.append(chatMsgDict)

            jsonPath = idBakPath / f"chat_{qqId}.json"
            jsonStr = Utility.getJsonStr(jsonObj)
            jsonPath.write_text(jsonStr, encoding="utf-8")

        return True

    def extractMedia(self) -> bool:
        """
        从数据库读取图片
        """
        for qqId, qqChatList in self.idMsgDict.items():
            self.callback(False, f"正在提取{qqId}中的文件...")
            idBakPath = self.outputDir / self.BAK_DIR / qqId
            idBakPath.mkdir(parents=True, exist_ok=True)

            for qqChat in qqChatList:
                if len(qqChat.dbFileResId) == 0:
                    continue
                for resId in qqChat.dbFileResId:
                    fileBytes = self.__queryResById(resId)
                    if len(fileBytes) == 0:
                        continue

                    fileExt = Utility.getFileExtByBytes(fileBytes)
                    filePath = idBakPath / f"{resId}{fileExt}"
                    filePath.write_bytes(fileBytes)

        for dbUtil in self.resDbUtil:
            dbUtil.close()

        return True

    def copyUserDir(self) -> bool:
        """
        解密dat文件
        """
        return True

    def __getDatabaseType(self, tableName):
        if tableName[0:3] == "msg":
            return self.TABLE_MSG
        elif tableName == "resfile":
            return self.TABLE_RES_FILE
        elif tableName[0:3] == "res":
            return self.TABLE_RES
        elif tableName == "filecontext":
            return self.TABLE_FILE_CONTEXT

    def __readDatabaseInternal(self, dbUtil: DBUtil, dbType: int, tableName: str):
        _, execData = dbUtil.exec(f"select * from {tableName}")
        if dbType == self.TABLE_MSG:
            for msgData in execData:
                # msgData[7]应该是QByteArray
                qqId = msgData[2]
                qqChat = QQChat(msgData[0], msgData[7].data(), msgData[5], msgData[2], msgData[4], [])
                Utility.addListInDict(self.idMsgDict, qqId, qqChat)
        elif dbType == self.TABLE_RES:
            qqId = tableName.split("_")[-1]
            if qqId not in self.idResDict.keys():
                self.idResDict[qqId] = {}

            for resData in execData:
                msgSeq = resData[0]
                resInfoId = resData[7]
                Utility.addListInDict(self.idResDict[qqId], msgSeq, resInfoId)

        elif dbType == self.TABLE_FILE_CONTEXT:
            for fileContext in execData:
                resId = fileContext[0]
                dbFileResId = fileContext[11]
                self.fileContextDict[resId] = dbFileResId

    def __queryResById(self, resId: str) -> bytes:
        for dbUtil in self.resDbUtil:
            execRes, execData = dbUtil.exec("select * from resfile where resId = ?", resId)
            if not execRes:
                continue
            else:
                return execData[0][1].data()

        log.d(f"All db not found {resId}")
        return bytes()


@dataclass
class WeComMessage:
    conversationId: str
    senderId: str
    sendTime: str
    content: bytes


# noinspection SqlResolve
class WeComSerializer(AppSerializer):
    def __init__(self, account: Account):
        super(WeComSerializer, self).__init__(account)
        self.messageDict: Dict[str, List[WeComMessage]] = {}  # conversationId:WeComMessage
        self.contactDict: Dict[str, str] = {}  # WeComId:Name
        self.serviceDict: Dict[str, str] = {}  # ServiceConversationId : Name

    def readDatabase(self) -> bool:
        dbNames = ["decrypt_" + dbName for dbName in ["message.db", "user.db", "session.db"]]
        for dbName in dbNames:
            if not (self.outputDir / dbName).exists():
                self.callback(True, "数据库解密不完整。")
                return False

        dbMessage = DBUtil(str((self.outputDir / dbNames[0]).resolve()))
        dbUser = DBUtil(str((self.outputDir / dbNames[1]).resolve()))
        dbSession = DBUtil(str((self.outputDir / dbNames[2]).resolve()))

        self.callback(False, "正在读取Message.db...")
        execRes, dataRes = dbMessage.exec("select conversation_id, sender_id, send_time, content "
                                          "from message_table order by send_time")
        for data in dataRes:
            msg = WeComMessage(data[0], str(data[1]), data[2], data[3].data())
            Utility.addListInDict(self.messageDict, msg.conversationId, msg)

        self.callback(False, "正在读取User.db...")
        execRes, dataRes = dbUser.exec("select id, name from user_table")
        for data in dataRes:
            self.contactDict[str(data[0])] = data[1]

        self.callback(False, "正在读取Session.db...")
        execRes, dataRes = dbSession.exec("select id, name from conversation_table where length(name) > 0")
        for data in dataRes:
            self.serviceDict[data[0]] = data[1]

        return True

    def outputJson(self) -> bool:
        for conversationId, weComMsgList in self.messageDict.items():
            self.callback(False, f"正在将{conversationId}聊天记录序列化...")
            jsonObj = []
            chatType = self.__getChatType(conversationId)
            chatName = self.__getChatName(conversationId)

            for weComMsg in weComMsgList:
                msgStart = weComMsg.content.rfind(0x0a) + 1 if chatType != 2 else 0

                jsonObj.append({
                    "Sender": self.contactDict.get(weComMsg.senderId, "未知用户") if chatType != 2
                    else self.serviceDict.get(weComMsg.conversationId, "未知服务号"),
                    "Time": Utility.getFormatTime(float(weComMsg.sendTime)),
                    "Content": self._decodeUtf8(weComMsg.content[msgStart:])
                })
            jsonPath = self.outputDir / (chatName + ".json")
            jsonPath.write_text(Utility.getJsonStr(jsonObj), encoding="utf-8")
        return True

    def extractMedia(self) -> bool:
        return True

    def copyUserDir(self) -> bool:
        dirPicked = ["Avator", "Cache", "WeDrive"]
        srcFileStoragePath = pathlib.Path(self.account.path) / self.account.uid
        dstFileStoragePath = self.outputDir

        if not srcFileStoragePath.exists():
            return True

        # 复制文件到输出目录
        for dirName in dirPicked:
            dirPath = srcFileStoragePath / dirName
            dstPath = dstFileStoragePath / dirName
            dstPath.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dirPath, dstPath, dirs_exist_ok=True)

        return True

    def __getChatType(self, convId: str):
        # match convId[0]:
        #     case "S":
        #         return 0
        #     case _:
        #         return 1

        if convId[0] == "S":  # 个人聊天:
            return 0
        elif convId[0] == "R":  # 群聊
            return 1
        else:
            return 2

    def __getChatName(self, convId: str) -> str:
        if self.__getChatType(convId) == 0:
            chatId1 = convId[2:].split("_")[0]
            chatId2 = convId[2:].split("_")[1]
            chatName1 = self.contactDict.get(chatId1, "未知用户" + chatId1)
            chatName2 = self.contactDict.get(chatId2, "未知用户" + chatId2)
            return chatName1 + "_" + chatName2
        else:
            return self.serviceDict.get(convId, "未知服务号" + convId[2:])
