# coding: utf-8
import string
import re
import time
import googletrans
import hfapi
import jieba
import jieba.analyse
import requests
from awaits.awaitable import awaitable


from random import choice
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
def TestHit(query: str, *keylist) -> int:
    # query_set = GenerateJieba(query)
    # keys = GenerateJieba(doc['Keyword'])
    # keys |= GenerateJieba(doc['Summarization'])
    # if len(query_set & keys) > 0 or query in doc['Content']:
    #     # hit
    #     return True
    # return False
    QuerySet = re.sub(f"[{punc}\n]+", "", query)
    QuerySet = {w for w in jieba.cut(query)} - stop_words
    QuerySet.add(query)

    keylist = sorted(keylist, key=len)
    ALL_MAX = 0
    for Key in keylist:
        if Key == "":
            continue
        Key = re.sub(f"[{punc}\n]+", "", Key)
        KeySet = {w for w in jieba.analyse.extract_tags(Key, topK=7)}
        KeySet = KeySet - stop_words
        KeySet.add(Key)

        rst = QuerySet & KeySet
        sum = 0
        for r in rst:
            sum += len(r)
        ALL_MAX = max(ALL_MAX, sum)
    return ALL_MAX


@awaitable()
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
    try:
        return rst[0]["summary_text"]
    except KeyError:
        time.sleep(3)  # sec
        return TextSummarization(content)


IC_provider = [
    'https://hf.space/embed/awacke1/NLPImageUnderstanding/+/api/predict',
    "https://hf.space/embed/OFA-Sys/OFA-Image_Caption/+/api/predict/",
    "https://hf.space/embed/jonasmouyal/Image_Captioning/api/predict",
]


@awaitable()
def ImageCaptioning(encoded_image: str) -> str:
    for space_url in IC_provider:
        try:
            r = requests.post(
                url=space_url,
                json={"data": [f"data:image/jpeg;base64,{encoded_image}"]}
            )
            cap = r.json()['data'][0]
            break
        except:
            logger.info(f"image captioning failed! response: {r.json()}")
            cap = ""
    if cap == "":
        return ""
    zhTW = Translator.translate(cap, dest="zh-TW", src='en').text
    return zhTW
