from db.db_util import DBUtil
from login.login_ui import LoginWidget
from util.tools import MD5Tool


class LoginController:
    def __init__(self, loginWidget: LoginWidget):
        self.widget = loginWidget
        self.user = None

    def login(self, name: str, pwd: str):
        if len(name.strip()) == 0 or len(pwd.strip()) == 0:
            self.widget.onLoginFinish(False, "请输入用户名或密码")
            return

        dbUtil = DBUtil(autoClose=False)
        success, resList = dbUtil.exec(DBUtil.SQL_QUERY_USER, name)

        if success:
            if MD5Tool.getMD5(pwd) == resList[0][1]:
                self.widget.onLoginFinish(True, None)
                self.user = name
                dbUtil.exec(DBUtil.SQL_UPDATE_USER_LOGGED, 1, name)
                dbUtil.close()
                return
            else:
                self.widget.onLoginFinish(False, "密码错误")
                dbUtil.close()
                return

        self.widget.onLoginFinish(False, "用户未注册")


        a = 0x0 / 0


    def logout(self):
        if self.user is not None:
            dbUtil = DBUtil()
            dbUtil.exec(DBUtil.SQL_UPDATE_USER_LOGGED, 0, self.user)
            self.widget.onLogout(self.user)
