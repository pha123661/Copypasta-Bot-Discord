# coding: utf-8
import interactions
import pymongo
import random
import heapq

import config
from config import logger
from database import *
from vlp import TestHit
from utils import *


class commands_update(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command()
    @interactions.option(description="要抽幾篇, 預設爲1", min_value=1, max_value=10)
    async def random(self, ctx: interactions.CommandContext, number: int = 1):
        """隨機從資料庫抽取 ”number“ 篇, 預設爲 1 篇"""
        async def send_random(col: pymongo.collection.Collection, CN):
            random_idx = random.randint(0, CN - 1)  # [0, CN)
            doc = col.find_one(skip=random_idx)
            if doc is not None:
                to_send = f"幫你從{CN}篇中精心選擇了「{doc['Keyword']}」"
                if doc['Type'] == 1:
                    to_send += f":\n{doc['Content']}"
                    await ctx.channel.send(to_send)
                elif doc['Type'] == 2:
                    img = GetImg(doc, doc['Summarization'])
                    await ctx.channel.send(to_send, files=img)
                else:
                    return await send_random(col, CN)
            else:
                await ctx.channel.send('發生錯誤')

        if ChatStatus[int(ctx.guild_id)].Global:
            col = GLOBAL_COL
        else:
            col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]

        CN = col.estimated_document_count()
        if CN == 0:
            await ctx.send("資料庫沒東西是在抽屁")
            return
        await ctx.send(f"以下爲抽取{number}篇的結果：")
        await ctx.get_channel()
        number = min(number, CN)
        for i in range(number):
            await send_random(col, CN)
            if i != number - 1:
                await ctx.channel.send('-' * 10)

    @interactions.extension_command()
    @interactions.option(description="搜尋關鍵字")
    async def search(self, ctx: interactions.CommandContext, query: str):
        """在資料庫的 “摘要” “關鍵字” 和 “內容” 中進行搜尋"""
        if ChatStatus[int(ctx.guild_id)].Global:
            col = GLOBAL_COL
        else:
            col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]
        cursor = col.find(filter={"Type": {"$ne": 0}}, cursor_type=pymongo.CursorType.EXHAUST).sort(
            "Type", pymongo.ASCENDING)

        await ctx.defer()
        Maximum_Rst = 10
        Rst_Count = 0
        heap = list()  # max heap
        for doc in cursor:
            if doc['Type'] == 1:
                priority = await TestHit(query, doc['Keyword'], doc['Content'])
            else:
                priority = await TestHit(query, doc['Keyword'], doc['Summarization'])
            if priority > 0:
                heapq.heappush(heap, PriorityEntry(
                    priority, doc))

        for _ in range(len(heap)):
            if Rst_Count >= Maximum_Rst:
                Rst_Count += 1
                break

            tmp = heapq.heappop(heap)
            priority, doc = tmp.priority, tmp.data

            Rst_Count += 1
            to_send = f"{'-'*10}\n關鍵字:「{doc['Keyword']}」\n摘要:「{doc['Summarization']}」"
            if doc['Type'] == 1:
                to_send += f":\n{doc['Content']}"
                await ctx.author.send(to_send)
            elif doc['Type'] == 2:
                img = GetImg(doc, doc['Summarization'])
                await ctx.author.send(to_send, files=img)
            else:
                Rst_Count -= 1

        if Rst_Count > Maximum_Rst:
            # exceeded
            Rst_Count -= 1
            await ctx.send("搜尋結果超過上限25筆, 只顯示前25筆, 請嘗試更換關鍵字")

        await ctx.send(f"「{query}」的搜尋結果共 {Rst_Count} 筆, 請查看與 bot 的私訊")
        await ctx.author.send(f"「{query}」的搜尋結果共 {Rst_Count} 筆")
        cursor.close()
        logger.info(f"search query: “{query}” with {Rst_Count} results")

    @interactions.extension_command()
    @interactions.option(description="要顯示幾篇, 預設爲3", min_value=1, max_value=10)
    async def recent(self, ctx: interactions.CommandContext, number: int = 3):
        """顯示公共資料庫最新加入的 ”number“ 篇, 預設爲 3 篇"""
        if not ChatStatus[int(ctx.guild_id)].Global:
            await ctx.send("執行失敗: 此指令只能在公共模式下執行")
            return
        await ctx.defer()
        col = GLOBAL_COL
        sort = [("CreateTime", pymongo.DESCENDING)]
        filter = {"From": {"$ne": int(ctx.author.id)}}
        Curser = col.find(filter, limit=number, sort=sort)
        for idx, doc in enumerate(Curser):
            if idx == 0:
                await ctx.get_channel()
                SENDER = ctx
            else:
                SENDER = ctx.channel
                await SENDER.send('-' * 10)
            to_send = [
                f"來自：「{await GetMaskedNameByID(self.client, doc['From'])}」",
                f"名稱：「{doc['Keyword']}」",
                f"摘要：「{doc['Summarization']}」"
            ]
            if doc['Type'] == 1:
                to_send.append(f"內容:「{doc['Content']}」")
                await SENDER.send("\n".join(to_send))
            elif doc['Type'] == 2:
                img = GetImg(doc, doc['Summarization'])
                await SENDER.send("\n".join(to_send), files=img)
            else:
                to_send.append("內容:「不支援的檔案格式 (可能來自telegram)」")
                await SENDER.send("\n".join(to_send))
        logger.info(f"get recent {number}")


def setup(client):
    commands_update(client)
