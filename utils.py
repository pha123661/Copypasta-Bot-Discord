import interactions
import io
import requests
from database import *


def GetImgByURL(URL: str, description: str = None) -> interactions.File:
    img = interactions.File(
        filename=f"img.jpg",
        fp=io.BytesIO(requests.get(URL).content),
        description=description
    )
    return img


def LinkTGAccount(DCUserID: int, TGUserID: int) -> bool:
    global UserStatus
    col = GLOBAL_DB[CONFIG['DB']['USER_STATUS']]

    tg_info = col.find_one({"TGUserID": TGUserID})
    if tg_info is None:
        return False
    elif col.find_one({"DCUserID": DCUserID, "TGUserID": {"$exists": True}}):
        return False

    filter = {"DCUserID": DCUserID}

    if tg_info.get("Nickname") != None:
        update = {
            "$set": {"TGUserID": TGUserID, "Nickname": tg_info["Nickname"]},
            "$inc": {"Contribution": tg_info['Contribution']}
        }
    else:
        update = {
            "$set": {"TGUserID": TGUserID},
            "$inc": {"Contribution": tg_info['Contribution']}
        }

    try:
        dc_old_info = col.find_one_and_update(
            filter=filter, update=update, upsert=True)
        UserStatus[DCUserID].TGUserID = TGUserID
        UserStatus[DCUserID].Contribution = dc_old_info['Contribution'] + \
            tg_info['Contribution']
        col.find_one_and_delete({"_id": tg_info['_id']})

        return True
    except:
        return False


async def GetLBInfo(client, num: int) -> str:
    sort = [('Contribution', pymongo.DESCENDING)]
    cursor = GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find(limit=num, sort=sort)
    LB = ["目前KO榜:"]
    for idx, doc in enumerate(cursor, 1):
        Username = await GetMaskedNameByID(client, doc.get('DCUserID'))
        LB.append(f"{idx}. {Username}, 貢獻值:{doc['Contribution']}")
    return '\n'.join(LB)


async def GetMaskedNameByID(client, DCUserID: int) -> str:
    if DCUserID is None:
        return "Telegram 用戶"

    doc = GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find_one(
        {"DCUserID": DCUserID})

    if doc.get("Nickname") != None:
        return doc['Nickname']

    Name = await interactions.get(client, interactions.User, object_id=DCUserID)
    Name = Name.username
    Mask = '*' * max(len(Name) // 3, 1)
    UnmaskIdx = (len(Name) - len(Mask)) // 2
    return ''.join([Name[:UnmaskIdx], Mask, Name[UnmaskIdx + len(Mask):]])
