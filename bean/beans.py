from dataclasses import dataclass


@dataclass
class Account:
    uid: str
    profile: str
    type: int
    active: bool = False
    keyDb: str = ""
    keyBak: str = ""
    time: int = 0
    path: str = ""


@dataclass
class SocialConfig:
    WECOM = 0
    WECHAT = 1
    QQ = 2
    DEFAULT = 3

    type: int
    status: bool
    path: str
    versions: str


AppList = {"微信": SocialConfig.WECHAT,
           "腾讯QQ": SocialConfig.QQ,
           "企业微信": SocialConfig.WECOM}

AppTypeToName = {
    SocialConfig.WECHAT: "微信",
    SocialConfig.QQ: "腾讯QQ",
    SocialConfig.WECOM: "企业微信"
}
