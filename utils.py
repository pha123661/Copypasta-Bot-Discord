# coding: utf-8
import interactions
import io
from database import *
import telegram
import os
import dotenv
import aiohttp


from config import logger

dotenv.load_dotenv()
tgbot = telegram.Bot(os.getenv("APITGTOKEN"))


async def GetImgByURL(URL: str, description: str = None) -> interactions.File:
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            try:
                resp.raise_for_status()
            except Exception as e:
                logger.error(e)
                return None
            img = interactions.File(
                filename=f"img.jpg",
                fp=io.BytesIO(await resp.content.read()),
                description=description
            )
    return img


async def GetImg(doc: dict(), description: str = "") -> interactions.File:
    if doc.get("Platform") == "Telegram" or doc.get("Platform") is None:
        try:
            URL = tgbot.getFile(doc['Content']).file_path
        except Exception as e:
            logger.error(e)
            if 'URL' in doc:
                return await GetImgByURL(doc['URL'], description)
    else:
        URL = doc['URL']
    return await GetImgByURL(URL, description)


async def LinkTGAccount(DCUserID: int, TGUserID: int) -> bool:
    global UserStatus
    col = GLOBAL_DB[CONFIG['DB']['USER_STATUS']]
    tg_info = await col.find_one({"TGUserID": TGUserID})
    if tg_info is None:
        return False
    elif await col.find_one({"DCUserID": DCUserID, "TGUserID": {"$exists": True}}):
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
        new_info = await col.find_one_and_update(
            filter=filter, update=update, upsert=True, return_document=pymongo.ReturnDocument.AFTER)
        UserStatus[DCUserID].TGUserID = TGUserID
        UserStatus[DCUserID].Contribution = new_info['Contribution']
        UserStatus[DCUserID].Nickname = new_info['Nickname']
        await col.find_one_and_delete({"_id": tg_info['_id']})
        return True
    except Exception as e:
        logger.error(e)
        return False


async def GetLBInfo(client, num: int) -> str:
    sort = [('Contribution', pymongo.DESCENDING)]
    cursor = GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find(limit=num, sort=sort)
    LB = ["目前KO榜:"]
    idx = 1  # async for can't enumerate
    async for doc in cursor:
        if 'Nickname' in doc:
            Username = doc['Nickname']
        else:
            Username = await GetMaskedNameByID(client, doc.get('DCUserID'))
        LB.append(f"{idx}. {Username}, 貢獻值:{doc['Contribution']}")
        idx += 1
    return '\n'.join(LB)


async def GetMaskedNameByID(client, FromID: int) -> str:
    if FromID is None:
        return "Telegram 用戶"

    doc = await GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find_one(
        {"$or": [{"DCUserID": FromID}, {"TGUserID": FromID}]})

    if doc is not None:
        if doc.get("Nickname") != None:
            return doc['Nickname']
        elif doc.get("DCUserID") != None:
            FromID = doc.get("DCUserID")
    try:
        Name = await interactions.get(client, interactions.User, object_id=FromID)
    except Exception as e:
        return "Telegram 用戶"

    Name = Name.username
    Mask = '*' * max(len(Name) // 3, 1)
    UnmaskIdx = (len(Name) - len(Mask)) // 2
    return ''.join([Name[:UnmaskIdx], Mask, Name[UnmaskIdx + len(Mask):]])


def argmax(pairs):
    # given an iterable of pairs return the key corresponding to the greatest value
    return max(pairs, key=lambda x: x[1])[0]


def argmax_index(values):
    # given an iterable of values return the index of the greatest value
    return argmax(enumerate(values))
