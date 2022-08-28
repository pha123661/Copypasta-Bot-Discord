import interactions
import pymongo
from pprint import pprint
from datetime import datetime, timezone

import config
from config import CONFIG, logger
from database import *
from utils import *


class commands_public(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="Telegram 的 使用者ID, 可以在 Telegram 對 bot 輸入 /userid 以取得")
    async def linktg(self, ctx: interactions.CommandContext, tguserid: int):
        """和 Telegram 帳號進行連結, 兩個帳號可共享貢獻值"""
        await ctx.defer()
        if await LinkTGAccount(int(ctx.author.id), tguserid):
            await ctx.send(f"連結Telegram成功, 馬上用status查看吧")
            logger.info(
                f"link successfully: DC: {int(ctx.author.id)} and TG: {tguserid}")
        else:
            await ctx.send("發生錯誤, 可能是 Telegram 帳號不存在 / 已完成過連結, 不是的話請找作者")
            logger.warning(
                f"link failed: DC: {int(ctx.author.id)} and TG: {tguserid}")

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="想要設定的暱稱, 設定後可以更改、不能刪除")
    async def nickname(self, ctx: interactions.CommandContext, nickname: str):
        """設定自己的暱稱, 跨平台時才能顯示哦! (不然會是“DC使用者”)"""
        if not 1 <= len(nickname) <= 7:
            await ctx.send(f"設定失敗: 暱稱不能大於7個字, 目前{len(nickname)}字")
            return
        await ctx.defer()
        DCUserID = int(ctx.author.id)
        GLOBAL_DB[CONFIG['DB']['USER_STATUS']].find_one_and_update(
            filter={"DCUserID": DCUserID}, update={"$set": {"Nickname": nickname}}, upsert=True)
        UserStatus[DCUserID].Nickname = nickname
        await ctx.send(f"設定暱稱「{nickname}」成功")
        logger.info(
            f"set nickname successfully: DCUserID: {DCUserID}, Nickname: {nickname}")

    @interactions.extension_command(dm_permission=False)
    async def toggle(self, ctx: interactions.CommandContext):
        """在 私人模式 和 公共模式 之間切換"""
        GuildID = int(ctx.guild_id)

        await ctx.defer()
        if ChatStatus.get(GuildID) is not None and ChatStatus.get(GuildID).Global:
            # public -> private
            ChatStatus.get(GuildID).Global = False
            await UpdateChatStatus(ChatStatus.get(GuildID))
            await ctx.send("切換成功, 已關閉公共模式")
            return

        if ChatStatus.get(GuildID) is None:
            content = """第一次進入公共模式，請注意：
1. 這裡的資料庫是所有人共享的
2. 只能刪除自己新增的東西
3. 我不想管裡面有啥 但你亂加東西讓我管 我就ban你
4. 可以再次使用 /toggle 來退出
5. 公共資料庫的內容和 Telegram 版本是共享的"""
            await ctx.send(content)
            logger.info(f"first time entering global mode Guild: {GuildID}")
            ChatStatus[GuildID] = ChatStatusEntity(GuildID=GuildID)

        UserID = int(ctx.author.id)
        # private -> public
        if UserStatus[UserID].Banned:
            await ctx.send("你被ban了 不能開啓公共模式 覺得莫名奇妙的話也一定是bug 請找作者💩")
            return
        ChatStatus[GuildID].Global = True
        await UpdateChatStatus(ChatStatus[GuildID])

        await ctx.send("切換成功, 已開啓公共模式")

    @interactions.extension_command(dm_permission=False)
    async def status(self, ctx: interactions.CommandContext):
        """查看目前模式 和 KO榜"""
        # get leaderboard
        await ctx.defer()
        DCUserID = int(ctx.author.id)
        GuildID = int(ctx.guild_id)
        ChanID = int(ctx.channel_id)

        Leaderboard = await GetLBInfo(self.client, 3)
        if UserStatus[DCUserID].Nickname != None:
            Nickname = UserStatus[DCUserID].Nickname
        else:
            Nickname = "尚未設定暱稱"

        # get status
        if ChatStatus[int(ctx.guild_id)].Global:
            guild_mode = "公共模式"
        else:
            guild_mode = "私人模式"

        if ChanID in ChatStatus[GuildID].DcDisabledChan:
            chan_mode = "閉嘴狀態"
        else:
            chan_mode = "bot會插嘴"

        # get current ranking
        Curser = GLOBAL_DB[CONFIG['DB']['USER_STATUS']].aggregate([
            {"$setWindowFields": {
                "sortBy": {"Contributions": -1},
                "output": {"globRnk": {"$rank": {}}}
            }},
            {"$match": {
                "DCUserID": int(ctx.author.id)
            }},
            {"$limit": 1}
        ])

        ranking = next(iter(Curser))['globRnk']
        if ranking <= 3:
            ranking = f"第 {ranking} 名, WOW 沒人生 🎉大家一起恭喜你🎉"
        elif ranking <= 10:
            ranking = f"第 {ranking} 名, 厲害了 前十名誒"
        else:
            ranking = f"第 {ranking} 名"

        await ctx.send("", embeds=interactions.Embed(
            title="狀態查詢",
            description=Leaderboard,
            thumbnail=interactions.EmbedImageStruct(
                url="https://imgur.com/lCHwufq.jpg"),
            color=0x406C96,
            timestamp=datetime.now(),
            footer=interactions.EmbedFooter(
                text="一大坨迷因感謝您的使用",
                icon_url="https://imgur.com/LdjownE.jpg",
            ),
            fields=[
                interactions.EmbedField(
                    name="伺服器狀態",
                    value=guild_mode,
                    inline=True
                ),
                interactions.EmbedField(
                    name="頻道狀態",
                    value=chan_mode,
                    inline=True,
                ),
                interactions.EmbedField(
                    name='暱稱',
                    value=Nickname,
                    inline=True
                ),
                interactions.Embed(
                    name='貢獻值',
                    value=UserStatus[DCUserID].Contribution,
                    inline=True
                ),
                interactions.Embed(
                    name='貢獻值排行',
                    value=ranking,
                    inline=True
                ),
            ]
        ))

    @ interactions.extension_command(dm_permission=False)
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

        Newcon = await AddContribution(DCUserID, con)
        await ctx.send(f"成功把{con}坨大便倒進公共資料庫, {'倒了個寂寞, 'if con == 0 else ''}目前累計貢獻{Newcon}坨")
        logger.info(
            f"dump successfully: con:{con} by DCUserID:{DCUserID}")


def setup(client):
    commands_public(client)
