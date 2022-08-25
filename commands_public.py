import interactions
import pymongo
from pprint import pprint
from datetime import datetime, timezone

import config
from config import CONFIG
from database import *
from vlp import GenerateJieba


class commands_public(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command()
    @interactions.option(description="Telegram 的 使用者ID, 可以在 Telegram 輸入 /UserID 以取得")
    async def linktg(self, ctx: interactions.CommandContext, userid: int):
        """和 Telegram 使用者進行連接, 可共享貢獻值"""
        pass

    @interactions.extension_command()
    async def toggle(self, ctx: interactions.CommandContext):
        """在 私人模式 和 公共模式 之間切換"""
        GuildID = int(ctx.guild_id)
        CSE = ChatStatus.get(GuildID)

        if CSE != None and CSE.Global:
            # public -> private
            CSE = ChatStatusEntity(GuildID=GuildID, Global=False)
            UpdateChatStatus(CSE)
            await ctx.send("切換成功, 已關閉公共模式")
            return

        if CSE == None:
            content = """第一次進入公共模式，請注意：
1. 這裡的資料庫是所有人共享的
2. 只能刪除自己新增的東西
3. 我不想管裡面有啥 但你亂加東西讓我管 我就ban你
4. 可以再次使用 /toggle 來退出
5. 公共資料庫的內容和 Telegram 版本是共享的"""
            await ctx.send(content)
        UserID = int(ctx.author.id)
        # private -> public
        if UserStatus[UserID].Banned:
            await ctx.send("你被ban了 不能開啓公共模式 覺得莫名奇妙的話也一定是bug 請找作者💩")
            return
        CSE = ChatStatusEntity(GuildID=GuildID, Global=True)
        UpdateChatStatus(CSE)

        await ctx.send("切換成功, 已開啓公共模式")

    @interactions.extension_command()
    async def status(self, ctx: interactions.CommandContext):
        """查看目前模式 和 KO榜"""
        # get leaderboard
        Leaderboard = await GetLBInfo(self.client, 3)
        # get status
        if ChatStatus[int(ctx.guild_id)].Global:
            await ctx.send(f"{Leaderboard}\n{'-'*10}\n目前處於 公共模式\n貢獻值爲{UserStatus[int(ctx.author.id)].Contribution}")
        else:
            await ctx.send(f"{Leaderboard}\n{'-'*10}\n目前處於 私人模式\n貢獻值爲{UserStatus[int(ctx.author.id)].Contribution}")

    @interactions.extension_command()
    async def dump(self, ctx: interactions.CommandContext):
        """將目前私人資料庫內由**自己**新增的內容複製到公共資料庫"""
        await ctx.defer()
        GuildID = int(ctx.guild_id)
        DCUserID = int(ctx.author.id)
        source_col = DB[config.GetColNameByGuildID(GuildID)]
        target_col = GLOBAL_COL

        filter = {"From": DCUserID}
        cursor = source_col.find(
            filter=filter, cursor_type=pymongo.CursorType.EXHAUST)
        docs2insert = list()
        for doc in cursor:
            del doc['_id']
            doc['CreateTime'] = datetime.now(timezone.utc)
            docs2insert.append(doc)
        if len(docs2insert) == 0:
            await ctx.send("傾卸失敗: 沒有東西能傾卸")
            return

        try:
            MRst = target_col.insert_many(docs2insert, ordered=False)
            con = len(MRst.inserted_ids)
        except pymongo.errors.BulkWriteError as bwe:
            con = bwe.details['nInserted']

        Newcon = AddContribution(DCUserID, con)
        await ctx.send(f"成功把{con}坨大便倒進公共資料庫, {'倒了個寂寞, 'if con == 0 else ''}目前累計貢獻{Newcon}坨")


def setup(client):
    commands_public(client)
