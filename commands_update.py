# coding: utf-8
import interactions
import pymongo
import base64
import asyncio
from typing import *
from hashlib import sha256
from bson.objectid import ObjectId
import aiohttp


import config
from config import CONFIG
from vlp import TextSummarization, ImageCaptioning
from database import *
from utils import *


class commands_update(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client
        self.QueuedDeletes = dict()

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="關鍵字,不宜過長或重複")
    @interactions.option(description="複製文, 和圖片擇一傳送即可, 長度 < 6 的複製文不會生成摘要")
    @interactions.option(description="圖片, 和複製文擇一傳送即可")
    async def add(self, ctx: interactions.CommandContext, keyword: str, content: str = None, media: interactions.api.models.message.Attachment = None):
        """新增複製文/圖"""
        if content is None and media is None:
            await ctx.send("新增失敗：請給我複製文或圖片", ephemeral=True)
            return
        if not 2 <= len(keyword) <= 30:
            await ctx.send(f"新增失敗：關鍵字長度需介於 2~30 字, 目前爲{len(keyword)}字", ephemeral=True)
            return
        if (content is not None) and not (1 <= len(content) <= 1900):
            await ctx.send(f"新增失敗：內容長度需介於1~1900字, 目前爲{len(content)}字", ephemeral=True)
            return
        await ctx.defer()
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
                async with aiohttp.ClientSession() as session:
                    async with session.get(URL) as response:
                        img_data = await response.content.read()
                encoded_image = base64.b64encode(img_data).decode('UTF-8')
                FileUniqueID = sha256(encoded_image.encode()).hexdigest()

            elif media.content_type.startswith("video"):
                await ctx.send(f"新增失敗: 附檔格式不支援{media.content_type}")
                return
            else:
                await ctx.send(f"新增失敗: 附檔格式不支援{media.content_type}")
                return

        GuildID = int(ctx.guild_id)
        FromID = int(ctx.author.id)
        if ChatStatus[GuildID].Global:
            Col = GLOBAL_COL
        else:
            Col = DB[config.GetColNameByGuildID(GuildID)]

        # check existing files
        Filter = {"$and": [{"Type": Type}, {
            "Keyword": keyword}, {"FileUniqueID": FileUniqueID}]}
        if await Col.find_one(Filter) is not None:
            # find duplicates
            await ctx.send("傳過了啦 腦霧?", ephemeral=True)
            return

        # insert
        if Type == CONFIG['SETTING']['TYPE']['TXT']:
            if len(content) <= 5:
                Summarization = ""
            else:
                Summarization = await TextSummarization(Content)

        elif Type == CONFIG['SETTING']['TYPE']['IMG']:
            Summarization = await ImageCaptioning(encoded_image)

        Rst = await InsertHTB(Col, {
            "Type": Type,
            "Keyword": keyword,
            "Summarization": Summarization,
            "Content": Content,
            "URL": URL,
            "From": FromID,
            "FileUniqueID": FileUniqueID,
        })

        if ChatStatus[GuildID].Global:
            await AddContribution(FromID, 1)

        # respond
        if Rst.acknowledged:
            # success
            to_send: List[str] = [f'新增「{keyword}」成功']
            if Summarization != "":
                to_send.append(f'自動生成的摘要爲:「{Summarization}」')
            else:
                to_send.append('未生成摘要')

            if Type == CONFIG['SETTING']['TYPE']['TXT']:
                if ChatStatus[GuildID].Global:
                    to_send.append(
                        f'目前貢獻值: {UserStatus[FromID].Contribution}')
                to_send.append(f'內容:「{Content}」')
                await ctx.send("\n".join(to_send))

            else:
                img = await GetImgByURL(media.proxy_url, Summarization)
                if ChatStatus[GuildID].Global:
                    to_send.append(
                        f'目前貢獻值: {UserStatus[FromID].Contribution}')
                await ctx.send("\n".join(to_send), files=img)
            logger.info(
                f"add successfully: Keyword: {keyword}, Summarization: {Summarization}")
        else:
            # failed
            await ctx.send(f'新增失敗 資料庫發生不明錯誤')
            logger.error(f"add failed: DB_S_Rst: {Rst}")

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="欲刪除複製文的關鍵字")
    async def delete(self, ctx: interactions.CommandContext, keyword: str):
        """刪除複製文, 若有重複關鍵字 最多只會顯示5篇"""
        if not 2 <= len(keyword) <= 30:
            await ctx.send(f"新增失敗：關鍵字長度需介於 2~30 字, 目前爲{len(keyword)}字", ephemeral=True)
            return
        await ctx.defer()
        if ChatStatus[int(ctx.guild_id)].Global:
            col = GLOBAL_COL
            filter = {"$and": [
                {"Keyword": keyword},
                {"From": int(ctx.author.id)}
            ]}
        else:
            col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]
            filter = {"Keyword": keyword}
        num = await col.count_documents(filter=filter)
        if num <= 0:
            await ctx.send(f'關鍵字「{keyword}」沒有東西可以刪除')
            return

        cursor = col.find(filter=filter).sort(
            "Type", pymongo.ASCENDING).limit(5)
        SOptions = list()
        async for doc in cursor:
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
    async def confirmation_handler(self, ctx: interactions.CommandContext, selected_values: List[str]):
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
            doc = await col.find_one(filter)
            if doc is None:
                await ctx.channel.send(f"找不到 {_id}, 請確認刪除時沒有切換模式")
            else:
                to_send: List[str] = [f"摘要:「{doc['Summarization']}」"]
                if doc['Type'] == 1:
                    if len(doc['Content']) >= 100:
                        content = doc['Content'][:97] + "……"
                    else:
                        content = doc['Content']
                    to_send.append(f"內容:「{content}」")
                    await ctx.channel.send("\n".join(to_send))
                elif doc['Type'] == 2:
                    img = await GetImg(doc, doc['Summarization'])
                    await ctx.channel.send("\n".join(to_send), files=img)
                else:
                    to_send.append("內容:「不支援的檔案格式 (可能來自Telegram)」")
                    await ctx.channel.send("\n".join(to_send))

            if doc is not None:
                return True
            else:
                return False

        await ctx.defer()
        try:
            await ctx.get_channel()
        except interactions.LibraryException:
            await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
            return

        await ctx.send(f"以下爲 {len(selected_values)} 筆的內容預覽:")

        self.QueuedDeletes[int(ctx.guild_id)] = selected_values
        try:
            for idx, _id in enumerate(self.QueuedDeletes[int(ctx.guild_id)], 1):
                await ctx.channel.send("-" * 4 + f" 第 {idx} 筆" + "-" * 4)
                await send_confirmation_by_id(_id)
        except interactions.LibraryException:
            await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
            return

        await ctx.channel.send(
            f"請確認是否刪除以上 {len(selected_values)} 筆內容?",
            components=interactions.ActionRow.new(
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
            )
        )

    @interactions.extension_component("deletion_cancel")
    async def deletion_candel(self, ctx: interactions.CommandContext):
        if int(ctx.guild_id) in self.QueuedDeletes:
            del self.QueuedDeletes[int(ctx.guild_id)]
        await ctx.edit("已取消刪除", components=interactions.ActionRow.new(
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY,
                label="是",
                custom_id='deletion',
                disabled=True,
            ),
            interactions.Button(
                style=interactions.ButtonStyle.SECONDARY,
                label="否",
                custom_id='deletion_cancel',
                disabled=True,
            )
        ))

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
            doc = await col.find_one_and_delete(filter)
            if doc is not None:
                return True
            else:
                return False

        if int(ctx.guild_id) not in self.QueuedDeletes:
            await ctx.send("別亂按la")
            return
        await ctx.defer()
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
