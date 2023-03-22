import json

from bean.beans import SocialConfig
from util.tools import UITool

WeComLink = UITool.generateVersionList(
    ("4.0.0.6024", "https://dldir1.qq.com/wework/work_weixin/WeCom_4.0.0.6024.exe")
)

WeChatLink = UITool.generateVersionList(
    ("3.4.0.38", "https://www.123pan.com/s/9TgRVv-WQO3A"),
    ("3.4.5.27", "https://www.123pan.com/s/9TgRVv-CQO3A"),
    ("3.6.0.18", "https://www.123pan.com/s/9TgRVv-BEO3A")
)

WeChatLinkDirectory = UITool.generateVersionList(
    ("点击下载", "https://www.123pan.com/s/9TgRVv-2EO3A")
)

QQLink = UITool.generateVersionList(
    ("9.5.5.28104", "https://www.123pan.com/s/9TgRVv-SQO3A")
)

DownloadInfo = {
    SocialConfig.WECOM: json.dumps(WeComLink),
    SocialConfig.WECHAT: json.dumps(WeChatLinkDirectory),
    SocialConfig.QQ: json.dumps(QQLink)
}


def getDescription() -> str:
    return f"适配版本：\n" \
           f"企业微信: {', '.join([d['version'] for d in WeComLink])}\n" \
           f"微信: {', '.join([d['version'] for d in WeChatLink])}\n" \
           f"腾讯QQ: {', '.join([d['version'] for d in QQLink])}\n"


if __name__ == '__main__':
    pass
