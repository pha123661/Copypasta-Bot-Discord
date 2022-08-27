# coding: utf-8
import interactions
import config
import heapq
import base64
from hashlib import sha256
from database import *
from config import CONFIG, logger
from vlp import TestHit, ImageCaptioning
from utils import *

if len(CONFIG['SETTING']['GUILD_IDs']) > 0:
    bot = interactions.Client(
        token=CONFIG['API']['DC']['TOKEN'],
        default_scope=CONFIG['SETTING']['GUILD_IDs'],
        intents=interactions.Intents.DEFAULT | interactions.Intents.GUILD_MESSAGE_CONTENT
    )
else:
    bot = interactions.Client(
        token=CONFIG['API']['DC']['TOKEN'],
        intents=interactions.Intents.DEFAULT | interactions.Intents.GUILD_MESSAGE_CONTENT
    )


def main():
    bot.load("commands_update")
    bot.load("commands_retrieval")
    bot.load("commands_public")
    bot.load("commands_management")
    bot.load('interactions.ext.files')
    bot.start()


@bot.event()
async def on_start():
    print(f"*** Sucessfully login as {bot.me.name} ***")
    await bot.change_presence(interactions.ClientPresence(
        activities=[interactions.PresenceActivity(name="你媽在叫", type=interactions.PresenceActivityType.LISTENING)]))


@bot.event()
async def on_message_create(msg: interactions.Message):
    """提到類似關鍵字時 bot 會插嘴"""
    if msg.author.id == bot.me.id or msg.content == '':
        return
    elif len(msg.attachments) == 0:
        if msg.channel_id in ChatStatus[int(msg.guild_id)].DcDisabledChan:
            return
        await text_normal_message(msg)
        return
    elif len(msg.attachments) == 1:
        await image_add_message(msg)


async def image_add_message(msg: interactions.Message):
    channel = await msg.get_channel()
    keyword = msg.content
    media = msg.attachments[0]
    # image
    if media.content_type.startswith("image") and media.content_type != "image/gif":
        Type = CONFIG['SETTING']['TYPE']['IMG']
        Content = media.proxy_url
        URL = media.url

        img_data = requests.get(URL).content
        encoded_image = base64.b64encode(img_data).decode('UTF-8')
        FileUniqueID = sha256(encoded_image.encode()).hexdigest()

    elif media.content_type.startswith("video"):
        await channel.send(f"新增失敗: 附檔格式不支援{media.content_type}")
        return
    else:
        await channel.send(f"新增失敗: 附檔格式不支援{media.content_type}")
        return

    to_be_deleted_msg = await msg.reply("運算中……")

    GuildID = int(msg.guild_id)
    FromID = int(msg.author.id)
    if ChatStatus[GuildID].Global:
        Col = GLOBAL_COL
    else:
        Col = DB[config.GetColNameByGuildID(GuildID)]

    # check existing files
    Filter = {"$and": [{"Type": Type}, {
        "Keyword": keyword}, {"FileUniqueID": FileUniqueID}]}
    if Col.find_one(Filter) is not None:
        # find duplicates
        await channel.send("傳過了啦 腦霧?", ephemeral=True)
        return

    # insert
    Summarization = ImageCaptioning(encoded_image)

    Rst = InsertHTB(Col, {
        "Type": Type,
        "Keyword": keyword,
        "Summarization": Summarization,
        "Content": Content,
        "URL": URL,
        "From": FromID,
        "FileUniqueID": FileUniqueID,
    })

    if ChatStatus[GuildID].Global:
        AddContribution(FromID, 1)

    # respond
    if Rst.acknowledged:
        # success
        to_send: List[str] = [f'新增「{keyword}」成功']
        if Summarization != "":
            to_send.append(f'自動生成的摘要爲:「{Summarization}」')
        else:
            to_send.append('未生成摘要')

        if Type == CONFIG['SETTING']['TYPE']['TXT']:
            to_send.append(f'內容:「{Content}」')
            if ChatStatus[GuildID].Global:
                to_send.append(
                    f'目前貢獻值: {UserStatus[FromID].Contribution}')
            await channel.send("\n".join(to_send))

        else:
            img = GetImgByURL(media.proxy_url, Summarization)
            if ChatStatus[GuildID].Global:
                to_send.append(
                    f'目前貢獻值: {UserStatus[FromID].Contribution}')
            await channel.send("\n".join(to_send), files=img)
    else:
        # failed
        await channel.send(f'新增失敗 資料庫發生不明錯誤')

    await to_be_deleted_msg.delete("運算完成, 刪除提示訊息")


async def text_normal_message(msg: interactions.Message):
    channel = await msg.get_channel()
    GuildID = int(msg.guild_id)
    Query = msg.content
    if ChatStatus[GuildID].Global:
        col = GLOBAL_COL
    else:
        col = DB[config.GetColNameByGuildID(GuildID)]

    filter = {"Type": {"$ne": 0}}
    sort = [('Type', pymongo.ASCENDING)]
    cursor = col.find(filter=filter, sort=sort)

    Candidates = list()  # max heap
    for doc in cursor:
        priority = TestHit(Query, doc['Keyword'], doc['Summarization'])
        priority /= len(Query)
        if priority >= CONFIG['SETTING']['BOT_TALK_THRESHOLD']:
            heapq.heappush(Candidates, PriorityEntry(priority, doc))
    if len(Candidates) <= 0:
        cursor.close()
        return

    tmp = heapq.heappop(Candidates)
    doc = tmp.data
    TestHit(Query, doc['Keyword'], doc['Summarization'])
    if doc['Type'] == 1:
        await channel.send(doc['Content'])
    elif doc['Type'] == 2:
        img = GetImg(doc, doc['Summarization'])
        await channel.send(files=img)

    cursor.close()

if __name__ == '__main__':
    main()
