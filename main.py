# coding: utf-8
from multiprocessing import Pool
import interactions
import heapq
import base64
import aiohttp
from hashlib import sha256

import config
from database import *
from utils import *
from commands_tutorial import tutorial_handler
from config import CONFIG, logger
from vlp import TestHit, ImageCaptioning


bot = interactions.Client(
    token=CONFIG['API']['DC']['TOKEN'],
    intents=interactions.Intents.DEFAULT | interactions.Intents.GUILD_MESSAGE_CONTENT
)


def main():
    bot.load("commands_update")
    bot.load("commands_retrieval")
    bot.load("commands_public")
    bot.load("commands_management")
    bot.load("commands_tutorial")
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
    if msg.author.bot or msg.author.id == bot.me.id or msg.content == '' or '@' in msg.content:
        return
    elif msg.guild_id is None:
        channel = await msg.get_channel()
        await channel.send("目前僅限在伺服器使用")
        return
    elif len(msg.attachments) == 0:
        if msg.channel_id in ChatStatus[int(msg.guild_id)].DcDisabledChan:
            return
        await text_normal_message(msg)
        return
    elif len(msg.attachments) == 1:
        await image_add_message(msg)
        return


@bot.event()
async def on_component(ctx: interactions.CommandContext):
    if ctx.data.custom_id.startswith("EXP "):
        await tutorial_handler(ctx, ctx.data.custom_id[4:])


@bot.event()
async def on_guild_create(guild: interactions.Guild):
    GuildID = int(guild.id)
    doc = await GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']].find_one({"GuildID": GuildID})
    if doc is None:
        await GLOBAL_DB[CONFIG['DB']['CHAT_STATUS']].insert_one({"GuildID": GuildID, "Global": False})
        chan = await interactions.get(bot, interactions.Channel,
                                      parent_id=guild.id, object_id=guild.system_channel_id)
        await chan.send("歡迎使用, 請使用 /example 查看教學, 或使用 /toggle 進入公共模式!")
        logger.info(
            f"Joined new guild: {guild}, ppl#: {guild.member_count}, guild_id: {guild.id}")


async def image_add_message(msg: interactions.Message):
    channel = await msg.get_channel()
    keyword = msg.content
    media = msg.attachments[0]
    # image
    if media.content_type.startswith("image") and media.content_type != "image/gif":
        Type = CONFIG['SETTING']['TYPE']['IMG']
        Content = media.proxy_url
        URL = media.url
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                img_data = await response.content.read()
        encoded_image = base64.b64encode(img_data).decode('UTF-8')
        FileUniqueID = sha256(encoded_image.encode()).hexdigest()

    elif media.content_type.startswith("video"):
        await channel.send(f"新增失敗: 附檔格式不支援{media.content_type}")
        return
    else:
        await channel.send(f"新增失敗: 附檔格式不支援{media.content_type}")
        return

    GuildID = int(msg.guild_id)
    FromID = int(msg.author.id)
    if ChatStatus[GuildID].Global:
        Col = GLOBAL_COL
    else:
        Col = DB[config.GetColNameByGuildID(GuildID)]

    # check existing files
    Filter = {"$and": [{"Type": Type}, {
        "Keyword": keyword}, {"FileUniqueID": FileUniqueID}]}
    if await Col.find_one(Filter) is not None:
        # find duplicates
        await channel.send("傳過了啦 腦霧?")
        return

    to_be_deleted_msg = await msg.reply("運算中……")
    # insert
    Summarization = await ImageCaptioning(encoded_image)

    Rst = await InsertHTB(Col, {
        "Type": Type,
        "Keyword": keyword,
        "Summarization": Summarization,
        "Content": Content,
        "URL": URL,
        "From": FromID,
        "FileUniqueID": FileUniqueID,
    })

    if ChatStatus[GuildID].Global:
        await AddContribution(FromID, 1)

    # respond
    if Rst.acknowledged:
        # success
        to_send: List[str] = [f'新增「{keyword}」成功']
        if Summarization != "":
            to_send.append(f'自動生成的摘要爲:「{Summarization}」')
        else:
            to_send.append('未生成摘要')

        if ChatStatus[GuildID].Global:
            to_send.append(f'目前貢獻值: {UserStatus[FromID].Contribution}')
        await channel.send("\n".join(to_send))
        logger.info(
            f"add successfully: Keyword: {keyword}, Summarization: {Summarization}")
    else:
        # failed
        await channel.send(f'新增失敗 資料庫發生不明錯誤')
        logger.error(f"add failed: DB_S_Rst: {Rst}")

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
    docs = await col.find(filter=filter, sort=sort).to_list(length=None)
    if len(docs) <= 0:
        return
    priorities = await asyncio.gather(
        *[TestHit(Query, doc['Keyword'], doc['Summarization']) for doc in docs])

    if max(priorities) / len(Query) < CONFIG['SETTING']['BOT_TALK_THRESHOLD']:
        return

    doc = docs[argmax_index(priorities)]

    if doc['Type'] == 1:
        await channel.send(doc['Content'])
    elif doc['Type'] == 2:
        img = await GetImg(doc, doc['Summarization'])
        await channel.send(files=img)
    logger.info(
        f"normal msg w/ priority of {max(priorities)/len(Query)}")


if __name__ == "__main__":
    main()
