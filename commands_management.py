import interactions
import pymongo
from pprint import pprint

import config
from config import CONFIG
from database import *
from utils import *


class command_management(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(dm_permission=False)
    @ctx_func_handler
    async def shutup(self, ctx: interactions.CommandContext):
        """在此頻道中禁止 bot 的插嘴功能 (再次使用可以重新啓用插嘴功能)"""
        GuildID = int(ctx.guild_id)
        ChanID = int(ctx.channel_id)

        if ChanID not in ChatStatus[GuildID].DcDisabledChan:
            ChatStatus[GuildID].DcDisabledChan.append(ChanID)
            await DisableDCChan(GuildID, ChanID)
            await ctx.send("我閉嘴了啦")
            return
        else:
            ChatStatus[GuildID].DcDisabledChan.remove(ChanID)
            await EnableDCChan(GuildID, ChanID)
            await ctx.send("我開始吵了哦")
            return


def setup(client):
    command_management(client)
