import json
from typing import List

from PyQt5.QtWidgets import QFileDialog

from bean.beans import SocialConfig
from db.db_util import DBUtil
from settings.settings_ui import BaseSettingsWidget
from util.app_download_info import DownloadInfo
from util.tools import UITool


class SettingsController:
    def __init__(self, widget: BaseSettingsWidget):
        self.widget = widget
        self.dbUtil = DBUtil()

    def getDefaultFilePath(self):
        try:
            path = self.dbUtil.exec(DBUtil.SQL_QUERY_SETTINGS)[1][SocialConfig.DEFAULT][1]
        except IndexError:
            return "%userprofile%"

        return path

    def getSettings(self) -> List[SocialConfig]:
        settings = self.dbUtil.exec(DBUtil.SQL_QUERY_SETTINGS)[1]
        configList = []
        for i, setting in enumerate(settings):  # setting is a list:[type, path, version_list]
            if i > 2:
                break
            versionJson = DownloadInfo[setting[0]]
            superLink = self.decodeVersionJson(versionJson)
            config = SocialConfig(i, True, setting[1], superLink)
            configList.append(config)

        return configList

    def changeFilePath(self, typ):
        path = QFileDialog.getExistingDirectory(self.widget, "选择文件夹", "/")
        if len(path) == 0:
            return
        dbUtil = DBUtil()
        dbUtil.exec(DBUtil.SQL_UPDATE_STORAGE, path, typ)
        self.widget.showOnFilePathChange(path, typ)

    @staticmethod
    def decodeVersionJson(versionJson) -> str:
        versionDict = {}
        jsonArr = json.loads(versionJson)
        for kv in jsonArr:
            version = kv["version"]
            link = kv["link"]
            versionDict[version] = link
        return UITool.getSuperLinkHtml(versionDict)
