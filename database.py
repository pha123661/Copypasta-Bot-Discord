import pymongo
from datetime import datetime
from config import CONFIG

# type HokTseBun struct {
#     UID           primitive.ObjectID `bson: "_id"`
#     Type          int                `bson: "Type"`
#     Keyword       string             `bson: "Keyword"`
#     Summarization string             `bson: "Summarization"`
#     Content       string             `bson: "Content"`
#     From          int64              `bson: "From"`
#     CreateTime    time.Time          `bson: "CreateTime"`
#     URL           string             `bson: "URL"`
#     FileUniqueID  string             `bson: "FileUniqueID"`
# *** Platform      string ***
# }


def InitDB() -> tuple[pymongo.database.Database, pymongo.database.Database]:
    client = pymongo.MongoClient(CONFIG['API']['MONGO']['URI'])
    DB = client[CONFIG['DB']['DB_NAME']]
    GLOBAL_DB = client[CONFIG['DB']['GLOBAL_DB_NAME']]

    # create default collections
    for ColName in (CONFIG['DB']['GLOBAL_COL'], CONFIG['DB']['CHAT_STATUS'], CONFIG['DB']['USER_STATUS']):
        if ColName in GLOBAL_DB.list_collection_names():
            continue
        GLOBAL_DB.create_collection(ColName)

    GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']].create_index(
        [("ChatID", pymongo.ASCENDING)], unique=True)
    GLOBAL_DB[CONFIG['DB']['USER_STATUS']].create_index(
        [("UserID", pymongo.ASCENDING)], unique=True)
    GLOBAL_DB[CONFIG['DB']['GLOBAL_COL']].create_indexes([
        pymongo.IndexModel("Type"),
        pymongo.IndexModel([("Type", pymongo.ASCENDING),
                            ("Keyword", pymongo.ASCENDING)]),
        pymongo.IndexModel([("Type", pymongo.ASCENDING),
                            ("Keyword", pymongo.ASCENDING),
                            ("FileUniqueID", pymongo.ASCENDING)],
                           unique=True)
    ])

    return GLOBAL_DB, DB


def InsertHTB(Collection: pymongo.database.Collection, HTB: dict) -> pymongo.results.InsertOneResult:
    """Inserts HTB and returns its result"""
    HTB['CreateTime'] = datetime.now()
    HTB['Platform'] = 'Discord'
    return Collection.insert_one(HTB)


GLOBAL_DB, DB = InitDB()
