import interactions
import config
import requests
import base64
from hashlib import sha256


from config import CONFIG
from utils import ChatStatus
from database import DB, GLOBAL_COL, InsertHTB
from vlp import TextSummarization, ImageCaptioning


class ModifyingCommands(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(description="新增複製文")
    @interactions.option(description="關鍵字,不宜過長或重複")
    @interactions.option(description="複製文, 和圖片擇一傳送即可")
    @interactions.option(description="圖片, 和複製文擇一傳送即可")
    async def add(self, ctx: interactions.CommandContext, keyword: str, copypasta: str = None, media: interactions.api.models.message.Attachment = None):
        if copypasta is None and media is None:
            await ctx.send("新增失敗：請給我複製文或圖片", ephemeral=True)
            return
        if not 2 <= len(keyword) <= 30:
            await ctx.send(f"新增失敗：關鍵字長度需介於 2~30 字, 目前爲{len(keyword)}字", ephemeral=True)
            return
        if (copypasta is not None) and not (1 <= len(copypasta) <= 1900):
            await ctx.send(f"新增失敗：內容長度需介於1~1900字, 目前爲{len(copypasta)}字", ephemeral=True)
            return

        # preprocess
        if media is None:
            # text
            Type = CONFIG['SETTING']['TYPE']['TXT']
            Content = copypasta
            URL = ""
            FileUniqueID = sha256(copypasta.encode()).hexdigest()

        else:
            # image
            if media.content_type.startswith("image") and media.content_type != "image/gif":
                Type = CONFIG['SETTING']['TYPE']['IMG']
                Content = media.proxy_url
                URL = media.url

                img_data = requests.get(URL).content
                encoded_image = base64.b64encode(img_data).decode('UTF-8')
                FileUniqueID = sha256(encoded_image.encode()).hexdigest()

            elif media.content_type.startswith("video"):
                await ctx.send(f"新增失敗: 附檔格式不支援{media.content_type}")
                return
            else:
                await ctx.send(f"新增失敗: 附檔格式不支援{media.content_type}")
                return

        if ChatStatus[ctx.guild_id].Global:
            Col = GLOBAL_COL
        else:
            Col = DB[config.GetColByGuildID(ctx.guild_id)]

        # check existing files
        Filter = {"$and": [{"Type": Type}, {
            "Keyword": keyword}, {"FileUniqueID": FileUniqueID}]}
        if Col.find_one(Filter) is not None:
            # find duplicates
            await ctx.send("傳過了啦 腦霧?", ephemeral=True)
            return

        await ctx.defer()
        # insert
        if Type == CONFIG['SETTING']['TYPE']['TXT']:
            Summarization = TextSummarization(Content)

        elif Type == CONFIG['SETTING']['TYPE']['IMG']:
            Summarization = ImageCaptioning(encoded_image)

        Rst = InsertHTB(Col, {
            "Type": Type,
            "Keyword": keyword,
            "Summarization": Summarization,
            "Content": Content,
            "URL": URL,
            "From": str(ctx.author.id),
            "FileUniqueID": FileUniqueID,
        })

        # respond
        if Rst.acknowledged:
            # success
            if Type == CONFIG['SETTING']['TYPE']['TXT']:
                await ctx.send(f'新增「{keyword}」成功\n自動生成的摘要爲:「{Summarization}」\n內容:「{Content}」')
            else:
                await ctx.send(f'新增「{keyword}」成功\n自動生成的摘要爲:「{Summarization}」')
                await ctx.send(media.proxy_url)
        else:
            # failed
            await ctx.send(f'新增失敗 資料庫發生不明錯誤')




def setup(client):
    ModifyingCommands(client)
