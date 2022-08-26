import os
import toml
from pprint import pprint


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


def GetColNameByGuildID(GuildID: int):
    return CONFIG['DB']['CFormat'] % GuildID


CONFIG = InitConfig("./config.toml")
