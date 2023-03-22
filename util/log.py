import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

logLevelDict = {
    0: logging.debug,
    1: logging.info,
    2: logging.warning,
    3: logging.error
}


def d(*args, sep=" "):
    print_log(getMsg(*args, sep=sep), 0)


def i(*args, sep=" "):
    print_log(getMsg(*args, sep=sep), 1)


def w(*args, sep=" "):
    print_log(getMsg(*args, sep=sep), 2)


def e(*args, sep=" "):
    print_log(getMsg(*args, sep=sep), 3)


def getMsg(*args, sep=" "):
    msg = ""
    for arg in args:
        msg += str(arg)
        msg += sep
    return msg


def print_log(msg, level):
    logLevelDict[level](msg)


if __name__ == '__main__':
    d("你好", "我叫Tim", sep="\n")
