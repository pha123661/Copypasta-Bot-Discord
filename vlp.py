import string
import re

import googletrans
import hfapi
import jieba
import requests

from random import choice
from config import CONFIG

# get stop_words for jieba
with open('./nlp_dict/chinese_stop_words.txt', encoding="utf-8") as f:
    stop_words = {line.strip() for line in f.readlines()}
punc = string.punctuation + \
    "！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏."
jieba.add_word("笑死")

HFclient = hfapi.Client(choice(CONFIG['API']['HF']['TOKENs']))
Translator = googletrans.Translator()


def GenerateJieba(keyword: str) -> set[str]:
    keyword = re.sub(f"[{punc}\n]+", "", keyword)
    ret = {w for w in jieba.cut_for_search(keyword)} - stop_words
    return ret


def TextSummarization(content: str) -> str:
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
            HFclient = hfapi.Client(choice(CONFIG['API']['HF']['TOKENs']))

        break

    return rst[0]["summary_text"]


def ImageCaptioning(encoded_image: str) -> str:
    r = requests.post(
        url='https://hf.space/embed/OFA-Sys/OFA-Image_Caption/+/api/predict/',
        json={"data": [f"data:image/jpeg;base64,{encoded_image}"]}
    )
    zhTW = Translator.translate(
        r.json()['data'][0], dest="zh-TW", src='en').text
    return zhTW
