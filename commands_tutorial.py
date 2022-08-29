import os
import interactions
from config import CONFIG


class commands_tutorial(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command()
    async def example(self, ctx: interactions.CommandContext):
        """觀看 bot 的使用說明"""
        components = [
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.PRIMARY,
                    label="這個 bot 是幹嘛用的",
                    custom_id='EXP WHATISTHIS',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="我要如何新增複製文?",
                    custom_id='EXP HOWTXT',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="我要如何新增圖片?",
                    custom_id='EXP HOWMEDIA',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="什麼是私人/公共資料庫?",
                    custom_id='EXP WHATISPUBLIC',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/add",
                    custom_id='EXP ADD',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/delete",
                    custom_id='EXP DEL',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/random",
                    custom_id='EXP RAND',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/search",
                    custom_id='EXP SERC',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/toggle",
                    custom_id='EXP TOG',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/recent",
                    custom_id='EXP RCNT',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/status",
                    custom_id='EXP STAT',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/nickname",
                    custom_id='EXP NICK',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/linktg",
                    custom_id='EXP LINK',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/dump",
                    custom_id='EXP DUMP',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/shutup",
                    custom_id='EXP STUP',
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.DANGER,
                    label="取消",
                    custom_id='EXP CANCL',
                ),
            ),
        ]

        def chunk(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        for idx, sp_com in enumerate(chunk(components, 4)):
            if idx == 0:
                try:
                    await ctx.get_channel()
                except interactions.LibraryException:
                    await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
                    return
                await ctx.send("請選擇要觀看的說明", components=sp_com)
            else:
                try:
                    await ctx.channel.send(components=sp_com)
                except interactions.LibraryException:
                    await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")


async def tutorial_handler(ctx: interactions.CommandContext, command: str) -> None:
    """Sends tutorial"""
    if command == "CANCL":
        await ctx.edit("已取消觀看教學, 因爲技術限制 上面那排收不起來 笑死", components=[])
        return
    with open(os.path.join(CONFIG['SETTING']['EXAMPLE_TXT_DIR'], f"{command}.txt"), mode='r', encoding='utf8') as f:
        try:
            img = interactions.File(filename=os.path.join(
                CONFIG['SETTING']['EXAMPLE_PIC_DIR'], f"{command}.jpg"))
            await ctx.send(f.read(), files=img)
        except FileNotFoundError:
            await ctx.send(f.read())


def setup(client):
    commands_tutorial(client)
