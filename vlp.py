# coding: utf-8
import re
import string
import time
from random import choice

import aiohttp
import googletrans
import hfapi
import jieba
import jieba.analyse
from awaits.awaitable import awaitable

from config import CONFIG, logger

# get stop_words for jieba
with open('./nlp_dict/chinese_stop_words.txt', encoding="utf-8") as f:
    stop_words = {line.strip() for line in f.readlines()}
punc = string.punctuation + \
    "！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏."
jieba.add_word("笑死")

HFclient = hfapi.Client(choice(CONFIG['API']['HF']['TOKENs']))
Translator = googletrans.Translator()


@awaitable()
def TestHit(query: str, *key_list) -> float:
    query = re.sub(f"[{punc}\n]+", "", query)
    query_set = {w for w in jieba.cut_for_search(query)} \
        & {w for w in jieba.analyse.extract_tags(query, topK=7)} \
        - stop_words
    query_set.add(query)

    key_list = sorted(key_list, key=len)
    ALL_MAX = 0.0
    for key in key_list:
        if key in query and len(key) > 1 and len(query) > 1:
            return 1.0
        key = re.sub(f"[{punc}\n]+", "", key)
        if len(key) == 0:
            continue
        key_set = {w for w in jieba.analyse.extract_tags(key, topK=7)}
        key_set = key_set - stop_words
        key_set.add(key)

        rst = query_set & key_set
        sum = 0
        for r in rst:
            sum += len(r)
        sum = max(sum / len(query), sum / len(key))
        ALL_MAX = max(ALL_MAX, sum)
    return ALL_MAX


@awaitable()
def TextSummarization(content: str) -> str:
    for _ in range(5):
        try:
            global HFclient
            count = len(CONFIG['API']['HF']['TOKENs'])
            for _ in range(count):
                try:
                    rst = HFclient.summarization(
                        input=content,
                        model=CONFIG['API']['HF']['SUM_MODEL']
                    )

                except Exception as e:
                    CONFIG['API']['HF']['TOKENs'].remove(HFclient.api_token)
                    if len(CONFIG['API']['HF']['TOKENs']) == 0:
                        return str(e)
                    HFclient = hfapi.Client(
                        choice(CONFIG['API']['HF']['TOKENs']))

                break
            return rst[0]["summary_text"]

        except KeyError:
            logger.info(f"TextSum key error, rst: {rst}")
            time.sleep(3)  # sec
    return ""


IC_provider = [
    "https://hf.space/embed/OFA-Sys/OFA-Image_Caption/+/api/predict/",
    "https://hf.space/embed/awacke1/NLPImageUnderstanding/+/api/predict",
    "https://hf.space/embed/jonasmouyal/Image_Captioning/api/predict",
]


async def ImageCaptioning(encoded_image: str) -> str:
    for space_url in IC_provider:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(space_url, json={"data": [f"data:image/jpeg;base64,{encoded_image}"]}) as resp:
                    j = await resp.json()
                    cap = j['data'][0]
                    break
        except Exception as e:
            logger.info(
                f"image captioning failed, err:{e}, response: {j}, url: {space_url}")
            cap = ""
    if cap == "":
        return ""
    zhTW = Translator.translate(cap, dest="zh-TW", src='en').text
    return zhTW
