import interactions
import pymongo
import requests
import base64
import asyncio
from hashlib import sha256
from bson.objectid import ObjectId

import config
from config import CONFIG
from database import DB, GLOBAL_COL, InsertHTB, ChatStatus, AddContribution
from vlp import TextSummarization, ImageCaptioning


class commands_update(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client
        self.QueuedDeletes = dict()

    @interactions.extension_command()
    @interactions.option(description="關鍵字,不宜過長或重複")
    @interactions.option(description="複製文, 和圖片擇一傳送即可, 長度 < 6 的複製文不會生成摘要")
    @interactions.option(description="圖片, 和複製文擇一傳送即可")
    async def add(self, ctx: interactions.CommandContext, keyword: str, content: str = None, media: interactions.api.models.message.Attachment = None):
        """新增複製文"""
        if content is None and media is None:
            await ctx.send("新增失敗：請給我複製文或圖片", ephemeral=True)
            return
        if not 2 <= len(keyword) <= 30:
            await ctx.send(f"新增失敗：關鍵字長度需介於 2~30 字, 目前爲{len(keyword)}字", ephemeral=True)
            return
        if (content is not None) and not (1 <= len(content) <= 1900):
            await ctx.send(f"新增失敗：內容長度需介於1~1900字, 目前爲{len(content)}字", ephemeral=True)
            return

        # preprocess
        if media is None:
            # text
            Type = CONFIG['SETTING']['TYPE']['TXT']
            Content = content
            URL = ""
            FileUniqueID = sha256(content.encode()).hexdigest()

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

        if ChatStatus[int(ctx.guild_id)].Global:
            Col = GLOBAL_COL
        else:
            Col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]

        # check existing files
        Filter = {"$and": [{"Type": Type}, {
            "Keyword": keyword}, {"FileUniqueID": FileUniqueID}]}
        if Col.find_one(Filter) is not None:
            # find duplicates
            await ctx.send("傳過了啦 腦霧?", ephemeral=True)
            return

        # insert
        if Type == CONFIG['SETTING']['TYPE']['TXT']:
            if len(content) <= 5:
                Summarization = ""
            else:
                await ctx.defer()
                Summarization = TextSummarization(Content)

        elif Type == CONFIG['SETTING']['TYPE']['IMG']:
            await ctx.defer()
            Summarization = ImageCaptioning(encoded_image)

        Rst = InsertHTB(Col, {
            "Type": Type,
            "Keyword": keyword,
            "Summarization": Summarization,
            "Content": Content,
            "URL": URL,
            "From": int(ctx.author.id),
            "FileUniqueID": FileUniqueID,
        })

        if ChatStatus[int(ctx.guild_id)].Global:
            AddContribution(int(ctx.author.id), 1)

        # respond
        if Rst.acknowledged:
            # success
            if Type == CONFIG['SETTING']['TYPE']['TXT']:
                if not Summarization == "":
                    await ctx.send(f'新增「{keyword}」成功\n自動生成的摘要爲:「{Summarization}」\n內容:\n{Content}')
                else:
                    await ctx.send(f'新增「{keyword}」成功\n未生成摘要\n內容:\n{Content}')
            else:
                await ctx.send(f'新增「{keyword}」成功\n自動生成的摘要爲:「{Summarization}」\n內容:\n{media.proxy_url}')
        else:
            # failed
            await ctx.send(f'新增失敗 資料庫發生不明錯誤')

    @interactions.extension_command()
    @interactions.option(description="欲刪除複製文的關鍵字")
    async def delete(self, ctx: interactions.CommandContext, keyword: str):
        """刪除複製文, 若有重複關鍵字 最多只會顯示5篇"""
        if not 2 <= len(keyword) <= 30:
            await ctx.send(f"新增失敗：關鍵字長度需介於 2~30 字, 目前爲{len(keyword)}字", ephemeral=True)
            return

        if ChatStatus[int(ctx.guild_id)].Global:
            col = GLOBAL_COL
            filter = {"$and": [
                {"Keyword": keyword},
                {"From": int(ctx.author.id)}
            ]}
        else:
            col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]
            filter = {"Keyword": keyword}
        num = col.count_documents(filter=filter)
        if num <= 0:
            await ctx.send(f'關鍵字「{keyword}」沒有東西可以刪除')
            return

        cursor = col.find(filter=filter).sort(
            "Type", pymongo.ASCENDING).limit(5)
        SOptions = list()
        for doc in cursor:
            SOption = interactions.SelectOption(
                label=f"{CONFIG['SETTING']['NAME'][doc['Type']]}：{doc['Keyword']}",
                value=f"{doc['_id']}",
                description=doc['Summarization']
            )
            SOptions.append(SOption)
        SMenu = interactions.SelectMenu(
            custom_id="deletion_confirmation",
            options=SOptions,
            min_values=1,
            max_values=len(SOptions),
        )
        await ctx.send("請選擇要刪除以下哪些:", components=SMenu)

    @interactions.extension_component("deletion_confirmation")
    async def confirmation_handler(self, ctx: interactions.CommandContext, selected_values: list[str]):
        async def send_confirmation_by_id(_id: str) -> bool:
            if ChatStatus[int(ctx.guild_id)].Global:
                col = GLOBAL_COL
                filter = {"$and": [
                    {"_id": ObjectId(_id)},
                    {"From": int(ctx.author.id)}
                ]}
            else:
                col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]
                filter = {"_id": ObjectId(_id)}
            doc = col.find_one(filter)
            if doc is None:
                await ctx.send(f"找不到 {_id}, 請確認刪除時沒有切換模式")
            else:
                await ctx.send(f"摘要:「{doc['Summarization']}」\n內容:\n{doc['Content']}")
            if doc is not None:
                return True
            else:
                return False

        self.QueuedDeletes[int(ctx.guild_id)] = selected_values
        for _id in self.QueuedDeletes[int(ctx.guild_id)]:
            await send_confirmation_by_id(_id)

        await ctx.send("請確認是否刪除以上內容?", components=interactions.ActionRow.new(
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY,
                label="是",
                custom_id='deletion',
            ),
            interactions.Button(
                style=interactions.ButtonStyle.SECONDARY,
                label="否",
                custom_id='deletion_cancel',
            )
        ))

    @interactions.extension_component("deletion_cancel")
    async def deletion_candel(self, ctx: interactions.CommandContext):
        if int(ctx.guild_id) in self.QueuedDeletes:
            del self.QueuedDeletes[int(ctx.guild_id)]
        await ctx.send("我其實不會把按鈕關掉 沒按也沒差 笑死")

    @interactions.extension_component("deletion")
    async def deletion_handler(self, ctx: interactions.CommandContext):
        async def delete_from_col_by_id(_id: str) -> bool:
            if ChatStatus[int(ctx.guild_id)].Global:
                col = GLOBAL_COL
                filter = {"$and": [
                    {"_id": ObjectId(_id)},
                    {"From": int(ctx.author.id)}
                ]}
            else:
                col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]
                filter = {"_id": ObjectId(_id)}
            doc = col.find_one_and_delete(filter)
            if doc is not None:
                return True
            else:
                return False

        if int(ctx.guild_id) not in self.QueuedDeletes:
            await ctx.send("別亂按la")
            return

        scheduled_tasks = []
        for _id in self.QueuedDeletes[int(ctx.guild_id)]:
            task = asyncio.create_task(delete_from_col_by_id(_id))
            scheduled_tasks.append(task)
        rets = await asyncio.gather(*scheduled_tasks)

        del self.QueuedDeletes[int(ctx.guild_id)]

        if all(rets):
            await ctx.send(f"刪除成功 {len(rets)} 筆")
        else:
            await ctx.send(f"刪除成功 {len([r for r in rets if r])} 筆, 失敗 {len([f for f in rets if not f])} 筆")


def setup(client):
    commands_update(client)
