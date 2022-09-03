import os
import interactions
from utils import ctx_func_handler
from config import CONFIG
from interactions.ext.persistence import PersistentCustomID, PersistenceExtension, extension_persistent_component


class commands_tutorial(PersistenceExtension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client
        self.what_components = [
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.PRIMARY,
                    label="這個 bot 是幹嘛用的",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="WHATISTHIS",
                    ))
                )
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="我要如何新增複製文?",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="HOWTXT",
                    ))
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="我要如何新增圖片?",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="HOWMEDIA",
                    ))
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="什麼是私人/公共資料庫?",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="WHATISPUBLIC",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SUCCESS,
                    label="👉觀看指令教學",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="TB_P_Swap",
                        package=1,
                    ))
                ),
            ),
        ]

        self.how_components = [
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.PRIMARY,
                    label="/add",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="ADD",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/delete",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="DEL",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/random",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="RAND",
                    ))
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/search",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="SERC",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/toggle",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="TOG",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/recent",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="RCNT",
                    ))
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/status",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="STAT",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/nickname",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="NICK",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/linktg",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="LINK",
                    ))
                ),
            ),
            interactions.ActionRow.new(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/dump",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="DUMP",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label="/shutup",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="Tutorial_Bottons",
                        package="STUP",
                    ))
                ),
                interactions.Button(
                    style=interactions.ButtonStyle.SUCCESS,
                    label="👈觀看功能介紹",
                    custom_id=str(PersistentCustomID(
                        cipher=self.client,
                        tag="TB_P_Swap",
                        package=0,
                    ))
                ),
            ),
        ]

        self.tutorial_pages = [self.what_components, self.how_components]

    @interactions.extension_command()
    @ctx_func_handler
    async def example(self, ctx: interactions.CommandContext):
        """觀看 bot 的使用說明和指令介紹"""
        try:
            await ctx.get_channel()
        except interactions.LibraryException:
            await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
            return
        await ctx.send("請選擇要觀看的說明", components=self.tutorial_pages[0])

    @extension_persistent_component("TB_P_Swap")
    async def TB_PageSwap(self, ctx: interactions.CommandContext, page: int) -> None:
        await ctx.edit(components=self.tutorial_pages[page])

    @extension_persistent_component("Tutorial_Bottons")
    async def tutorial_handler(self, ctx: interactions.CommandContext, command: str) -> None:
        """Sends tutorial"""
        if command == "CANCL":
            await ctx.edit("取消觀看教學", components=[])
            return
        with open(os.path.join(CONFIG['SETTING']['EXAMPLE_TXT_DIR'], f"{command}.txt"), mode='r', encoding='utf8') as f:
            try:
                img = interactions.File(filename=os.path.join(
                    CONFIG['SETTING']['EXAMPLE_PIC_DIR'], f"{command}.jpg"))
                await ctx.send(f.read(), files=img)
            except FileNotFoundError:
                await ctx.send(f.read())

    @interactions.extension_command()
    async def info(self, ctx: interactions.CommandContext) -> None:
        """取得bot的邀請連結 或和開發者聯繫(抱怨)"""
        embed = interactions.Embed(
            title="關於bot",
            description="""
            不管有任何意見, 抱怨, 建議 都可以直接寄信給我 OR 透過下方連結讓我知道哦
Email: `swli-iagents.9vj9n@slmail.me`""",
            url="https://github.com/pha123661/Hok_tse_bun_dcbot",
            footer=interactions.EmbedFooter(
                text="一大坨迷因感謝您的使用",
                icon_url="https://imgur.com/LdjownE.jpg",
            ),
        )
        await ctx.send(
            "",
            embeds=embed,
            components=[
                interactions.ActionRow.new(
                    interactions.Button(
                        style=interactions.ButtonStyle.LINK,
                        label="邀請 bot",
                        url=r"https://discord.com/api/oauth2/authorize?client_id=1011172667426095125&permissions=534723951680&scope=applications.commands%20bot"
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.LINK,
                        label='Telegram 版本',
                        url=r'https://t.me/HokTseBunBot'
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.LINK,
                        label="我的主頁",
                        url=r"https://github.com/pha123661"
                    ),
                    interactions.Button(
                        style=interactions.ButtonStyle.LINK,
                        label="功能建議",
                        url=r"https://github.com/pha123661/Hok_tse_bun_dcbot/issues"
                    ),
                ),
            ]
        )


def setup(client):
    commands_tutorial(client)
