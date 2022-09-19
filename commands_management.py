import urllib
from math import ceil

import interactions

from config import CONFIG
from database import *
from utils import *


class command_management(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(dm_permission=False)
    @ctx_func_handler
    @ext_cmd_ban_checker
    async def shutup(self, ctx: interactions.CommandContext):
        """在此頻道中禁止 bot 的插嘴功能 (再次使用可以重新啓用插嘴功能)"""
        GuildID = int(ctx.guild_id)
        ChanID = int(ctx.channel_id)

        if ChanID not in ChatStatus[GuildID].DcDisabledChan:
            ChatStatus[GuildID].DcDisabledChan.append(ChanID)
            await DisableDCChan(GuildID, ChanID)
            await ctx.send("我閉嘴了啦")
            guild = await ctx.get_guild()
            logger.info(f"shutup in {guild}, ppl#: {guild.member_count}")
            return
        else:
            ChatStatus[GuildID].DcDisabledChan.remove(ChanID)
            await EnableDCChan(GuildID, ChanID)
            await ctx.send("我開始吵了哦")
            return

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="上面的字")
    @interactions.option(description="下面的字")
    @ctx_func_handler
    @ext_cmd_ban_checker
    async def emomeme(self, ctx: interactions.CommandContext, top: str, bottom: str):
        """幫你製作出太他媽emo啦"""
        pic_url = get_emo_pic(top, bottom)
        await ctx.send(pic_url)


def get_emo_pic(top_word, bottom_word) -> str:
    url = "https://yurafuca.com/5000choyen/result.html?"
    top_length, bottom_length = 0, 0
    top_len_dict = keydefaultdict(
        lambda c: 0.6 if c.islower() or c.isdecimal() else 1.0,
        {
            'W': 1.3,

            'm': 0.9,
            'w': 0.9,

            'f': 0.3,
            'i': 0.3,
            'I': 0.3,
            'j': 0.3,
            'l': 0.3,
            't': 0.3,

            ' ': 0.2,
        }
    )
    for c in top_word:
        top_length += top_len_dict[c]

    for c in bottom_word:
        bottom_length += top_len_dict[c]

    bx = (top_length - 1) * 100
    width = (top_length + bottom_length - 2) * 100 + 100
    if top_length <= 2 or bottom_length <= 2:
        bx += 100
        width += 100
    payload = f"top={urllib.parse.quote(top_word)}&bottom={urllib.parse.quote(bottom_word)}&bx={ceil(bx)}&order=false&color=false&width={ceil(width)}&height=260"
    return url + payload


def setup(client):
    command_management(client)
