import string
import re
import functools
import googletrans
import hfapi
import jieba
import jieba.analyse
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


@functools.lru_cache(maxsize=512, typed=True)
def GenerateJieba(keyword: str, method, **kwargs) -> set[str]:
    keyword = re.sub(f"[{punc}\n]+", "", keyword)
    ret = {w for w in method(keyword, **kwargs)} - stop_words
    return ret


def TestHit(query: str, *keylist) -> bool:
    # query_set = GenerateJieba(query)
    # keys = GenerateJieba(doc['Keyword'])
    # keys |= GenerateJieba(doc['Summarization'])
    # if len(query_set & keys) > 0 or query in doc['Content']:
    #     # hit
    #     return True
    # return False
    QuerySet = GenerateJieba(query, jieba.cut)
    QuerySet.add(query)

    ALL_MAX = 0
    for Key in keylist:
        KeySet = GenerateJieba(query, jieba.analyse.extract_tags, topK=7)
        KeySet.add(Key)
        rst = QuerySet & KeySet
        sum = 0
        for r in rst:
            sum += len(r)
        ALL_MAX = max(ALL_MAX, sum)
    return ALL_MAX


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
