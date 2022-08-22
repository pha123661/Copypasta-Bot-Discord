import interactions
import config
from hashlib import sha256
from config import CONFIG
from utils import ChatStatus
from database import GLOBAL_DB, DB, InsertHTB
from vlp import TextSummarization


class ModifyingCommands(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(description="bot 會重複你說的話")
    @interactions.option(description="要回覆什麼?")
    async def echo(self, ctx: interactions.CommandContext, text: str):
        await ctx.send(f"bot 說了 {text}!")

    @interactions.extension_command(description="新增複製文")
    @interactions.autodefer(2.5)
    @interactions.option(description="關鍵字,不宜過長或重複")
    @interactions.option(description="複製文")
    @interactions.option(description="圖片")
    async def add(self, ctx: interactions.CommandContext, keyword: str, copypasta: str = None, media: interactions.api.models.message.Attachment = None):
        if copypasta is None and media is None:
            await ctx.send("新增失敗：請給我複製文或圖片", ephemeral=True)
            return
        if len(keyword) >= 30:
            await ctx.send(f"新增失敗：關鍵字長度需小於30字, 目前爲{len(keyword)}字", ephemeral=True)
            return
        if (copypasta is not None) and not (1 <= len(copypasta) <= 1900):
            await ctx.send(f"新增失敗：內容長度需介於1~1900字, 目前爲{len(copypasta)}字", ephemeral=True)
            return

        # get file type
        if media is None:
            Type = 1
            Content = copypasta
            Summarization = TextSummarization(Content)
            FileUniqueID = sha256(copypasta.encode()).hexdigest()
            URL = ""
        else:
            await ctx.send("目前尚未支援")
            return
            FileUniqueID = media.id
            # if media.content_type.startswith("image"):
            #     if media.content_type == "image/gif":
            #         Type = 3
            #     else:
            #         Type = 2
            # elif media.content_type.startswith("video"):
            #     Type = 4
            # else:
            #     await ctx.send(f"新增失敗: 附檔格式不支援{media.content_type}")
            #     return

        if ChatStatus[ctx.guild_id].Global:
            Col = GLOBAL_DB[CONFIG['DB']['GLOBAL_COL']]
        else:
            Col = DB[config.GetColByGuildID(ctx.guild_id)]

        # check existing files
        Filter = {"$and": [
            {"Type": Type},
            {"Keyword": keyword},
            {"FileUniqueID": FileUniqueID}
        ]}

        if Col.find_one(Filter) is not None:
            # find duplicates
            await ctx.send("傳過了啦 腦霧?", ephemeral=True)
            return

        Rst = InsertHTB(Col, {
            "Type": Type,
            "Keyword": keyword,
            "Summarization": Summarization,
            "Content": Content,
            "URL": URL,
            "From": str(ctx.author.id),
            "FileUniqueID": FileUniqueID,
        })

        if Rst.acknowledged:
            # success
            await ctx.send(f'新增「{keyword}」成功\n自動生成的摘要爲:「{Summarization}」\n內容:「{copypasta}」')
        else:
            # failed
            await ctx.send(f'新增失敗 資料庫發生不明錯誤')


def setup(client):
    ModifyingCommands(client)
