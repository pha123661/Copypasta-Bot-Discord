import interactions


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
                    label="我要如何新增圖片",
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
                    custom_id='EXP RANDOM',
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
                    label="/dump",
                    custom_id='EXP DUMP',
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/linktg",
                    custom_id='EXP LINK',
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
                await ctx.get_channel()
                await ctx.send("請選擇要觀看的說明", components=sp_com)
            else:
                await ctx.channel.send(components=sp_com)

    async def tutorial_buttons(self, ctx: interactions.CommandContext):
        print(ctx.callback, ctx.data.custom_id,
              ctx.message, ctx.type, ctx.token)
        interactions.Embed()


def setup(client):
    commands_tutorial(client)
