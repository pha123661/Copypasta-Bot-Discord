import pymongo
import interactions
import asyncio
from datetime import datetime
from collections import defaultdict
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
    def __init__(self, GuildID: int, Global: bool = False) -> None:
        self.GuildID: int = GuildID
        self.Global: int = Global


class UserStatusEntity:
    def __init__(self, DCUserID: int, Contribution: int = 0, Banned: bool = False) -> None:
        self.DCUserID: int = DCUserID
        self.Contribution: int = Contribution
        self.Banned: bool = Banned


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


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
        [("GuildID", pymongo.ASCENDING)], unique=True)
    GLOBAL_DB[CONFIG['DB']['USER_STATUS']].create_index(
        [("DCUserID", pymongo.ASCENDING), ("TGUserID", pymongo.ASCENDING)], unique=True)
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
        ChatStatus[doc['GuildID']] = ChatStatusEntity(
            GuildID=doc.get('GuildID'),
            Global=doc.get('Global'),
        )

    UserStatus = keydefaultdict(UserStatusEntity)
    for doc in GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find(cursor_type=pymongo.CursorType.EXHAUST):
        UserStatus[doc['DCUserID']] = UserStatusEntity(
            DCUserID=doc.get('DCUserID'),
            Contribution=doc.get('Contribution'),
            Banned=doc.get('Banned'),
        )

    return ChatStatus, UserStatus


def InsertHTB(Collection: pymongo.database.Collection, HTB: dict) -> pymongo.results.InsertOneResult:
    """Inserts HTB and returns its result"""
    HTB['CreateTime'] = datetime.now()
    HTB['Platform'] = 'Discord'
    return Collection.insert_one(HTB)


def UpdateChatStatus(CSE: ChatStatusEntity):
    """updates the chatstatus in db"""
    global ChatStatus
    col = GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']]
    filter = {"GuildID": CSE.GuildID}
    update = {"$set": {"Global": CSE.Global}}
    col.find_one_and_update(filter=filter, update=update, upsert=True)
    ChatStatus[CSE.GuildID] = CSE


def AddContribution(DCUserID: int, Delta: int) -> int:
    """increaments user contribution and returns current contribution"""
    global UserStatus, GLOBAL_DB
    col = GLOBAL_DB[CONFIG['DB']['USER_STATUS']]
    filter = {"DCUserID": DCUserID}
    update = {"$inc": {"Contribution": Delta}}
    doc = col.find_one_and_update(filter=filter, update=update, upsert=True)

    UserStatus[DCUserID].Contribution += 1
    return UserStatus[DCUserID].Contribution


async def GetLBInfo(client, num: int) -> str:
    sort = [('Contribution', pymongo.DESCENDING)]
    cursor = GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find(limit=num, sort=sort)
    LB = ["目前KO榜:"]
    for idx, doc in enumerate(cursor, 1):
        Username = await GetMaskedNameByID(client, doc.get('DCUserID'))
        LB.append(f"{idx}. {Username}, 貢獻值:{doc['Contribution']}")
    return '\n'.join(LB)


async def GetMaskedNameByID(client, DCUserID: int) -> str:
    async def GetName(client, DCUserID: int):
        if DCUserID is None:
            return "Telegram 用戶"
        ret = await interactions.get(client, interactions.User, object_id=DCUserID)
        ret = ret.username
        if ret is None:
            return "不明用戶"
        return ret
    Name = await GetName(client, DCUserID)
    Mask = '*' * max(len(Name) // 3, 1)
    UnmaskIdx = (len(Name) - len(Mask)) // 2
    return ''.join([Name[:UnmaskIdx], Mask, Name[UnmaskIdx + len(Mask):]])


GLOBAL_DB, DB, GLOBAL_COL = InitDB()
# ChatStatus[int(ctx.guild_id)] = ChatStatusEntity()
# UserStatus[int(ctx.author.id)] = UserStatusEntity()
ChatStatus, UserStatus = BuildCache()
