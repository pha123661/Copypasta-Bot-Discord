import toml
import os
from pprint import pprint


def InitConfig(path: str) -> dict:
    config = toml.load(path)
    config['API']['DC']['TOKEN'] = os.getenv("API.DC.TOKEN")
    config['API']['HF']['TOKENs'] = os.getenv("API.HF.TOKENs")
    config['API']['MONGO']['URI'] = os.getenv("API.MONGO.URI")
    config['DB']['DB_NAME'] = os.getenv("DB.DB_NAME")
    print("------------------------")
    print("Loaded config:")
    pprint(config)
    print("------------------------")
    return config


CONFIG = InitConfig("./config.toml")
GuildIDs = [948951282398416967]
