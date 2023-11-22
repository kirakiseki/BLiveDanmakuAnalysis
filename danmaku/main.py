import os
import logging
import sys
from dotenv import load_dotenv
from datetime import datetime
from bilibili_api import sync, settings, live, user, Credential
from bilibili_api.login import login_with_password, Check


class Logger:
    def __init__(self, name: str, level: str = "info"):
        formatter = logging.Formatter(
            "%(levelname)s - %(asctime)s — %(name)s: %(message)s"
        )

        self.logger = logging.getLogger(name=name)
        if level.lower() == "info":
            self.logger.setLevel(level=logging.INFO)
        else:
            self.logger.setLevel(level=logging.DEBUG)

        output_handler = logging.StreamHandler(sys.stdout)
        output_handler.setFormatter(formatter)
        self.logger.addHandler(output_handler)

        self.logger.propagate = False

    def getLogger(self):
        return self.logger


def init():
    global logger

    load_dotenv()

    logger = Logger(name="Danmaku Backend", level="info").getLogger()

    settings.geetest_auto_open = False


def login() -> Credential:
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    buvid3 = os.getenv("BUVID3")

    if not username or not password:
        logger.fatal("username or password undefined! Exiting...")
        exit(1)

    c = login_with_password(username, password)

    if isinstance(c, Check):
        logger.fatal("Need 2fa login! Exiting...")
        exit(-1)
    else:
        credential = c
        if not credential.has_buvid3():
            credential.buvid3 = buvid3

    return credential


def connect(room_num: int, credential: Credential):
    global room
    room = live.LiveDanmaku(room_num, credential=credential)

    @room.on('DANMU_MSG')
    async def on_danmaku(event):
        user = event['data']['info'][2][1]
        msg = event['data']['info'][1]
        timestamp = event['data']['info'][0][4]
        timestr = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"{timestr} Received danmaku from {user}: {msg}")

    @room.on('SEND_GIFT')
    async def on_gift(event):
        user = event['data']['data']['uname']
        gift_name = event['data']['data']['giftName']
        gift_price = event['data']['data']['price']
        num = event['data']['data']['num']
        timestamp = event['data']['data']['timestamp']
        timestr = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"{timestr} Received gift: {gift_name} x{num} from {user}, value: {num * gift_price}")

    sync(room.connect())


if __name__ == '__main__':
    init()
    logger.info("Danmaku Backend starting...")
    logger.info("Trying to login")
    credential = login()
    logger.info(f"Logged in: Welcome {sync(user.get_self_info(credential))['name']}")
    connect(55, credential)
