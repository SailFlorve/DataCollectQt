from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from util import log
from util.tools import MD5Tool

DEFAULT_DB = "./default.db"


class DBUtil:
    SQL_CREATE_USER = """
    create table if not exists user
    (
        name  TEXT not null
            primary key
            unique,
        pwd   TEXT not null,
        role  INT  not null,
        login integer
    );

    """

    SQL_CREATE_ACCOUNT = """
    create table if not exists account
    (
        uid     text    not null
            constraint keys_pk
                primary key,
        key_db  text    not null,
        key_bak text    not null,
        time    integer not null,
        type    integer,
        path    text,
        profile text,
        active  integer
    );
    """

    SQL_CREATE_SETTINGS = """
    create table if not exists settings
    (
        type         int
            constraint settings_pk
                primary key,
        path         int not null
    );
    """

    SQL_CREATE_APP_INSTALL = """
    create table app_install
    (
        type integer not null
            constraint app_install_pk
                primary key,
        path text
    );
    """

    SQL_CHECK_IF_TABLE_EXISTS = "select count(*) from sqlite_master where type='table' and name=?"

    SQL_QUERY_USER = "select * from user where name = ?"
    SQL_QUERY_ALL_USERS = "select * from settings"
    SQL_ADD_USER = "insert into user(name, pwd, role) values (?, ?, ?)"
    SQL_REMOVE_USER = "delete from user where name = ?"
    SQL_QUERY_USER_LOGGED = "select name from user where login = 1"
    SQL_UPDATE_USER_LOGGED = "update user set login = ? where name = ?"

    SQL_QUERY_ACCOUNT_BY_TYPE = "select * from account where type = ?"
    SQL_QUERY_ACCOUNT_BY_ID = "select * from account where uid = ?"
    SQL_ADD_ACCOUNT = "insert into account values (?, ?, ?, ?, ?, ?, ?, ?)"
    SQL_DELETE_ACCOUNT = "delete from account where uid = ?"
    SQL_ACTIVE_ACCOUNT = "update account set active = ?, key_db=?, key_bak=?, " \
                         "path=?, profile = ?, time=? " \
                         "where uid = ?"

    SQL_ADD_SETTINGS = "insert into settings values (?, ?)"
    SQL_QUERY_SETTINGS = "select * from settings"
    SQL_UPDATE_STORAGE = "update settings set path = ? where type = ?"

    SQL_ADD_APP_INSTALL_PATH = "insert into app_install values (?, ?)"
    SQL_DELETE_APP_INSTALL_PATH = "delete from app_install where type = ?"
    SQL_GET_APP_INSTALL_PATH = "select * from app_install where type = ?"

    def __init__(self, dbName: str = DEFAULT_DB, autoClose=True):
        self.dbName = dbName
        self.autoClose = autoClose
        self.db = QSqlDatabase.addDatabase("QSQLITE", dbName)
        self.db.setDatabaseName(dbName)

        self.__initDb()

    def __initDb(self):
        res = self.exec(self.SQL_CHECK_IF_TABLE_EXISTS, "user", needResult=False)
        if not res[0][0]:
            self.exec(self.SQL_CREATE_USER)
            self.exec(self.SQL_ADD_USER, "admin", MD5Tool.getMD5("admin"), 0)

        res = self.exec(self.SQL_CHECK_IF_TABLE_EXISTS, "account", needResult=False)
        if not res[0][0]:
            self.exec(self.SQL_CREATE_ACCOUNT)

        res = self.exec(self.SQL_CHECK_IF_TABLE_EXISTS, "settings", needResult=False)
        if not res[0][0]:
            self.exec(self.SQL_CREATE_SETTINGS)
            self.exec(self.SQL_ADD_SETTINGS, 0, "")
            self.exec(self.SQL_ADD_SETTINGS, 1, "")
            self.exec(self.SQL_ADD_SETTINGS, 2, "")
            self.exec(self.SQL_ADD_SETTINGS, 3, "%USERPROFILE%")

        res = self.exec(self.SQL_CHECK_IF_TABLE_EXISTS, "app_install", needResult=False)
        if not res[0][0]:
            self.exec(self.SQL_CREATE_APP_INSTALL)

    def open(self):
        if not self.db.isOpen():
            self.db.open()

    def close(self):
        self.db.close()

    def getQuery(self) -> QSqlQuery:
        return QSqlQuery(self.db)

    def exec(self, sql: str, *args, needResult=True, dictResult=False):
        """
        :param sql: .
        :param args: SQL语句中的值
        :param needResult: 是否需要执行是否成功的结果，如需要则返回值有两个，第一个为结果
        :param dictResult: 结果（每一行）是否为字典形式
        :return: 如果needResult为True则返回两个值，第一个为执行结果，如果查询失败或查询到的结果为空，则为False，否则为True;
                第二个为查询结果，如果查询失败或查询到的结果为空，则为空列表，否则为查询到的结果列表，列表中每一个元素还是列表，对应一行数据;
                即使只有一个结果，也是一个嵌套列表，形如[[...]];
                如果dictResult为True，则第二个返回值为字典列表，字典的key为列名，value为对应的值

        """
        self.open()
        query = self.getQuery()
        query.prepare(sql)
        for arg in args:
            query.addBindValue(arg)
        execRes = query.exec_()

        queryResult = []
        queryDictResult = []

        if not execRes:
            log.e(sql, args)
            log.e("Error:", query.lastError().text())
            return execRes, []

        while query.next():
            row = []
            rowDict = {}
            for i in range(query.record().count()):
                rowDict[query.record().field(i).name()] = query.value(i)
                row.append(query.value(i))
            queryResult.append(row)
            queryDictResult.append(rowDict)

        query.finish()

        if self.autoClose:
            self.close()

        if len(queryResult) == 0:
            execRes = False

        resultList = queryDictResult if dictResult else queryResult
        if needResult:
            return execRes, resultList
        else:
            return resultList


if __name__ == '__main__':
    util = DBUtil()
    r1, r2 = util.exec(DBUtil.SQL_QUERY_USER, "admin")
    log.i(r1, r2)
