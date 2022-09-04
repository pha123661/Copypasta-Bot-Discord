# coding: utf-8
import heapq
import random

import interactions
import pymongo

import config
from config import logger
from database import *
from utils import *
from vlp import TestHit


class commands_update(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="要抽幾篇, 預設爲1, 最大爲5", min_value=1, max_value=5)
    @ctx_func_handler
    @ext_cmd_ban_checker
    async def random(self, ctx: interactions.CommandContext, number: int = 1):
        """隨機從資料庫抽取 ”number“ 篇, 預設爲 1 篇"""
        async def send_random(col: pymongo.collection.Collection, CN):
            random_idx = random.randint(0, CN - 1)  # [0, CN)
            doc = await col.find_one(skip=random_idx)
            try:
                if doc is not None:
                    to_send = ["----------",
                               f"幫你從{CN}篇中精心選擇了「{doc['Keyword']}」"]
                    if doc['Type'] == 1:
                        to_send.append(f"內容:「{doc['Content']}」")
                        await ctx.channel.send("\n".join(to_send))
                    elif doc['Type'] == 2:
                        img = await GetImg(doc, doc['Summarization'])
                        if img is None:
                            return await send_random(col, CN)
                        await ctx.channel.send("\n".join(to_send), files=img)
                    else:
                        return await send_random(col, CN)
                else:
                    await ctx.channel.send('發生錯誤')
            except interactions.LibraryException:
                await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
                return

        if ChatStatus[int(ctx.guild_id)].Global:
            col = GLOBAL_COL
        else:
            col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]

        CN = await col.estimated_document_count()
        if CN == 0:
            await ctx.send("資料庫沒東西是在抽屁")
            return
        await ctx.send(f"以下爲抽取{number}篇的結果：")
        try:
            await ctx.get_channel()
        except interactions.LibraryException:
            await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
        await asyncio.gather(*[send_random(col, CN) for _ in range(number)])

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="搜尋關鍵字")
    @ctx_func_handler
    @ext_cmd_ban_checker
    async def search(self, ctx: interactions.CommandContext, query: str):
        """在資料庫的 “摘要” “關鍵字” 和 “內容” 中進行搜尋"""
        if ChatStatus[int(ctx.guild_id)].Global:
            col = GLOBAL_COL
        else:
            col = DB[config.GetColNameByGuildID(int(ctx.guild_id))]
        col_doc_count = await col.estimated_document_count()
        if col_doc_count <= 10:
            await ctx.send(
                f"警告: 當前資料庫只有 {col_doc_count} 筆資料, 如果想在公共資料庫查詢的話請使用 /toggle")
            logger.info("search in col with #doc <= 10")

        cursor = col.find(filter={"Type": {"$ne": 0}}, cursor_type=pymongo.CursorType.EXHAUST).sort(
            "Type", pymongo.ASCENDING)
        await ctx.defer()
        Maximum_Rst = 10
        Rst_Count = 0
        heap = list()  # max heap
        async for doc in cursor:
            if doc['Type'] == 1:
                priority = await TestHit(query, doc['Keyword'], doc['Summarization'], doc['Content'])
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
            to_send = [
                '----------',
                f"關鍵字:「{doc['Keyword']}」",
                f"摘要:「{doc['Summarization']}」",
            ]
            if doc['Type'] == 1:
                to_send .append(f"內容:「{doc['Content']}」")
                await ctx.author.send("\n".join(to_send))
            elif doc['Type'] == 2:
                img = await GetImg(doc, doc['Summarization'])
                if img is None:
                    await ctx.author.send("傳不出來 DC在搞")
                    continue
                await ctx.author.send("\n".join(to_send), files=img)
            else:
                Rst_Count -= 1

        if Rst_Count > Maximum_Rst:
            # exceeded
            Rst_Count -= 1
            await ctx.send("搜尋結果超過上限25筆, 只顯示前25筆, 請嘗試更換關鍵字")

        await ctx.send(f"「{query}」的搜尋結果共 {Rst_Count} 筆, 請查看與 bot 的私訊")
        await ctx.author.send(f"「{query}」的搜尋結果共 {Rst_Count} 筆")
        await cursor.close()
        logger.info(f"search query: “{query}” with {Rst_Count} results")

    @interactions.extension_command(dm_permission=False)
    @interactions.option(description="要顯示幾篇, 預設爲3, 最大爲5", min_value=1, max_value=5)
    @ctx_func_handler
    @ext_cmd_ban_checker
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
        idx = 0
        async for doc in Curser:
            if idx == 0:
                try:
                    await ctx.get_channel()
                except interactions.LibraryException:
                    await ctx.send("權限不足 可以踢掉重邀 邀請的時候請勾選要求的全部權限")
                    return
                SENDER = ctx
            else:
                SENDER = ctx.channel
            to_send = [
                f"來自：「{await GetMaskedNameByID(self.client, doc['From'])}」",
                f"名稱：「{doc['Keyword']}」",
                f"摘要：「{doc['Summarization']}」"
            ]
            if doc['Type'] == 1:
                to_send.append(f"內容:「{doc['Content']}」")
                await SENDER.send("\n".join(to_send))
            elif doc['Type'] == 2:
                img = await GetImg(doc, doc['Summarization'])
                if img is None:
                    await SENDER.send("傳不出來 DC在搞")
                await SENDER.send("\n".join(to_send), files=img)
            else:
                to_send.append("內容:「不支援的檔案格式 (可能來自telegram)」")
                await SENDER.send("\n".join(to_send))

            idx += 1

        logger.info(f"get recent {number}")


def setup(client):
    commands_update(client)
