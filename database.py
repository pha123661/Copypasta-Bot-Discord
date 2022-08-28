# coding: utf-8
import pymongo
from datetime import datetime
from collections import defaultdict
from typing import *
from awaits.awaitable import awaitable


from config import CONFIG

"""
type HokTseBun struct {
    UID
    Type          int
    Keyword       string
    Summarization string
    Content       string -> media.proxy_url
    From          string -> int(ctx.author.id)
    CreateTime    time.Time -> datatime.Now()
    URL           string -> media.url
    FileUniqueID  string -> sha256(Content / b64_encoded_image).hexdigit()
*** Platform      string -> "Discord" ***
}
"""


class ChatStatusEntity:
    def __init__(self, GuildID: int, ChatID: int = None, Global: bool = None, DcDisabledChan: List[int] = None) -> None:
        self.GuildID: int = GuildID
        self.ChatID: int = ChatID
        self.Global: int = Global
        if DcDisabledChan is None:
            self.DcDisabledChan: List[int] = list()
        else:
            self.DcDisabledChan: List[int] = DcDisabledChan


class UserStatusEntity:
    def __init__(self, DCUserID: int, TGUserID: int = None, Contribution: int = 0, Nickname: str = None, Banned: bool = False) -> None:
        self.DCUserID: int = DCUserID
        self.TGUserID: int = TGUserID
        self.Contribution: int = Contribution
        self.Nickname: str = Nickname
        self.Banned: bool = Banned


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


class PriorityEntry(object):

    def __init__(self, priority, data):
        self.data = data
        self.priority = priority

    def __lt__(self, other):
        return self.priority > other.priority  # max heap


def InitDB() -> Tuple[pymongo.database.Database, pymongo.database.Database]:
    client = pymongo.MongoClient(CONFIG['API']['MONGO']['URI'])
    DB = client[CONFIG['DB']['DB_NAME']]
    GLOBAL_DB = client[CONFIG['DB']['GLOBAL_DB_NAME']]

    # create default collections
    for ColName in (CONFIG['DB']['GLOBAL_COL'], CONFIG['DB']['CHAT_STATUS'], CONFIG['DB']['USER_STATUS']):
        if ColName in GLOBAL_DB.list_collection_names():
            continue
        GLOBAL_DB.create_collection(ColName)

    GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']].create_indexes([
        pymongo.IndexModel("GuildID"),
        pymongo.IndexModel("ChatID"),
        pymongo.IndexModel([("GuildID", pymongo.ASCENDING),
                            ('ChatID', pymongo.ASCENDING)],
                           unique=True),
    ])
    GLOBAL_DB[CONFIG['DB']['USER_STATUS']].create_indexes([
        pymongo.IndexModel("DCUserID"),
        pymongo.IndexModel("TGUserID"),
        pymongo.IndexModel([("DCUserID", pymongo.ASCENDING),
                            ('TGUserID', pymongo.ASCENDING)],
                           unique=True),
    ])
    GLOBAL_DB[CONFIG['DB']['GLOBAL_COL']].create_indexes([
        pymongo.IndexModel("Type"),
        pymongo.IndexModel([("Type", pymongo.ASCENDING),
                            ("Keyword", pymongo.ASCENDING)]),
        pymongo.IndexModel([("Type", pymongo.ASCENDING),
                            ("Keyword", pymongo.ASCENDING),
                            ("FileUniqueID", pymongo.ASCENDING)],
                           unique=True)
    ])

    return GLOBAL_DB, DB, GLOBAL_DB[CONFIG['DB']['GLOBAL_COL']]


def BuildCache():
    ChatStatus = keydefaultdict(ChatStatusEntity)
    for doc in GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']].find(cursor_type=pymongo.CursorType.EXHAUST):
        if 'GuildID' not in doc:
            continue
        ChatStatus[doc['GuildID']] = ChatStatusEntity(
            GuildID=doc.get('GuildID'),
            ChatID=doc.get('ChatID'),
            Global=doc.get('Global'),
            DcDisabledChan=doc.get('DcDisabledChan'),
        )

    UserStatus = keydefaultdict(UserStatusEntity)
    for doc in GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find(cursor_type=pymongo.CursorType.EXHAUST):
        if 'DCUserID' not in doc:
            continue
        UserStatus[doc['DCUserID']] = UserStatusEntity(
            DCUserID=doc.get('DCUserID'),
            TGUserID=doc.get('TGUserID'),
            Contribution=doc.get('Contribution'),
            Nickname=doc.get('Nickname'),
            Banned=doc.get('Banned'),
        )

    return ChatStatus, UserStatus


@awaitable
def InsertHTB(Collection: pymongo.database.Collection, HTB: dict) -> pymongo.results.InsertOneResult:
    """Inserts HTB and returns its result"""
    HTB['CreateTime'] = datetime.now()
    HTB['Platform'] = 'Discord'
    return Collection.insert_one(HTB)


@awaitable
def UpdateChatStatus(CSE: ChatStatusEntity):
    """updates the chatstatus in db"""
    global ChatStatus
    col = GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']]
    filter = {"GuildID": CSE.GuildID}
    update = {"$set": {"Global": CSE.Global}}
    col.find_one_and_update(filter=filter, update=update, upsert=True)
    ChatStatus[CSE.GuildID] = CSE


@awaitable
def AddContribution(DCUserID: int, Delta: int) -> int:
    """increaments user contribution and returns current contribution"""
    global UserStatus
    col = GLOBAL_DB[CONFIG['DB']['USER_STATUS']]
    filter = {"DCUserID": DCUserID}
    update = {"$inc": {"Contribution": Delta}}

    doc = col.find_one_and_update(
        filter=filter, update=update, upsert=True, return_document=pymongo.ReturnDocument.AFTER)
    UserStatus[DCUserID].Contribution = doc['Contribution']
    return UserStatus[DCUserID].Contribution


@awaitable
def DisableDCChan(GuildID: int, ChanID: int) -> bool:
    filter = {"GuildID": GuildID}
    update = {"$addToSet": {"DcDisabledChan": ChanID}}
    col = GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']]
    col.find_one_and_update(filter, update)
    return True


@awaitable
def EnableDCChan(GuildID: int, ChanID: int) -> bool:
    filter = {"GuildID": GuildID}
    update = {"$pull": {"DcDisabledChan": ChanID}}
    col = GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']]
    col.find_one_and_update(filter, update)
    return True


GLOBAL_DB: pymongo.database.Database
DB: pymongo.database.Database
GLOBAL_COL: pymongo.database.Collection
GLOBAL_DB, DB, GLOBAL_COL = InitDB()
# ChatStatus[int(ctx.guild_id)] = ChatStatusEntity()
# UserStatus[int(ctx.author.id)] = UserStatusEntity()
ChatStatus: List[ChatStatusEntity]
UserStatus: List[UserStatusEntity]
ChatStatus, UserStatus = BuildCache()
