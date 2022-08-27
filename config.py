import logging
import os
import toml
from pprint import pprint
import dotenv
import sys

dotenv.load_dotenv()


def InitConfig(path: str) -> dict:
    config = toml.load(path)
    config['API']['DC']['TOKEN'] = os.getenv("APIDCTOKEN")
    config['API']['HF']['TOKENs'] = (os.getenv("APIHFTOKENs")).split(" ")
    config['API']['MONGO']['URI'] = os.getenv("APIMONGOURI")
    config['DB']['DB_NAME'] = os.getenv("DBDB_NAME")
    config['DB']['GLOBAL_DB_NAME'] = os.getenv("DBGLOBAL_DB_NAME")
    print("------------------------")
    print("Loaded config:")
    pprint(config)
    print("------------------------")
    return config


def InitLogger(path: str) -> logging.Logger:
    logFormatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(module)-16s:%(lineno)-4s] %(message)s")

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler(path, encoding='utf8')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    return rootLogger


def GetColNameByGuildID(GuildID: int):
    return CONFIG['DB']['CFormat'] % GuildID


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


CONFIG = InitConfig("./config.toml")
logger = InitLogger(CONFIG['SETTING']['LOG_FILE'])
