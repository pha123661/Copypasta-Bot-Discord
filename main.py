# coding: utf-8
import interactions
import base64
import aiohttp
from hashlib import sha256
from interactions.ext.persistence import PersistentCustomID

import config
from database import *
from utils import *
from config import CONFIG, logger
from vlp import TestHit, ImageCaptioning
from commands_update import delete_from_col_by_id


bot = interactions.Client(
    token=CONFIG['API']['DC']['TOKEN'],
    intents=interactions.Intents.DEFAULT | interactions.Intents.GUILD_MESSAGE_CONTENT
)
bot.load('interactions.ext.files')
bot.load("interactions.ext.persistence",
         cipher_key=os.getenv("APIDCCIPHER"))
bot.load("commands_update")
bot.load("commands_retrieval")
bot.load("commands_public")
bot.load("commands_management")
bot.load("commands_tutorial")


def main():
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


# @bot.event()
# async def on_component(ctx: interactions.CommandContext):
#     if ctx.data.custom_id.startswith("EXP "):
#         await tutorial_handler(ctx, ctx.data.custom_id[4:])


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
    else:
        print(
            f"In guild: {guild.name}, ppl#: {guild.member_count}, guild_id: {guild.id}")


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

    sum_task = asyncio.create_task(ImageCaptioning(encoded_image))
    while True:
        task_name = id_generator()
        if task_name in task_dict:
            continue
        else:
            task_dict[task_name] = sum_task
            break
    to_be_deleted_msg = await msg.reply(
        "運算中……",
        components=interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            label="取消運算",
            custom_id=str(
                PersistentCustomID(
                    cipher=bot,
                    tag="cancel_task",
                    package=task_name,
                )
            )
        )
    )
    # insert
    Summarization = await sum_task

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
        to_be_modified_msg = await channel.send(
            "\n".join(to_send),
            components=interactions.Button(
                style=interactions.ButtonStyle.SECONDARY,
                label="阿幹手滑 我沒有要加這張",
                custom_id=str(PersistentCustomID(
                    cipher=bot,
                    tag="accidentally_delete",
                    package=str(Rst.inserted_id),
                ))
            ))
        logger.info(
            f"add successfully: Keyword: {keyword}, Summarization: {Summarization}")
    else:
        # failed
        await channel.send(f'新增失敗 資料庫發生不明錯誤')
        to_be_modified_msg = None
        logger.error(f"add failed: DB_S_Rst: {Rst}")

    await to_be_deleted_msg.delete("運算完成, 刪除提示訊息")
    if to_be_modified_msg is not None:
        await asyncio.sleep(30)
        await to_be_modified_msg.edit(components=[])


@bot.persistent_component("cancel_task")
async def cancel_task(ctx: interactions.CommandContext, task_name: str):
    try:
        task = task_dict[task_name]
        task.cancel()
        await ctx.edit("已取消", components=[])
    except Exception as e:
        await ctx.edit(f"取消失敗: {e}")


@bot.persistent_component("accidentally_delete")
async def handle_accidentally_image(ctx: interactions.CommandContext, _id: str):
    try:
        await delete_from_col_by_id(ctx, _id)
        await ctx.edit("刪除成功", components=[])
    except Exception as e:
        await ctx.edit(f"刪除失敗: {e}")


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

    if max(priorities) < CONFIG['SETTING']['BOT_TALK_THRESHOLD']:
        return

    doc = docs[argmax_index(priorities)]

    if doc['Type'] == 1:
        await channel.send(doc['Content'])
    elif doc['Type'] == 2:
        img = await GetImg(doc, doc['Summarization'])
        if img is None:
            return
        await channel.send(files=img)
    else:
        return
    guild = await msg.get_guild()
    logger.info(
        f"{guild.name}, #{guild.member_count}, Hit:{doc['Keyword']} normal msg w/ priority of {max(priorities)/len(Query)}")


if __name__ == "__main__":
    main()
