import interactions
import pymongo
import random

import config
from config import CONFIG
from database import DB, GLOBAL_COL, UpdateChatStatus, ChatStatus, ChatStatusEntity, UserStatus, UserStatusEntity, GetLBInfo
from vlp import GenerateJieba


class commands_public(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

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
4. 可以再次使用 /toggle 來退出"""
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


def setup(client):
    commands_public(client)
