# coding: utf-8
import interactions
import config
import heapq
from database import *
from config import CONFIG
from vlp import TestHit
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
    if len(msg.attachments) == 0:
        await text_normal_message(msg)


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
        img = GetImgByURL(doc['URL'], doc['Summarization'])
        await channel.send(files=img)

    cursor.close()

if __name__ == '__main__':
    main()
