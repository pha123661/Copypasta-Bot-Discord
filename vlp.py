import hfapi
import requests
import googletrans


from random import choice
from config import CONFIG

HFclient = hfapi.Client(choice(CONFIG['API']['HF']['TOKENs']))
Translator = googletrans.Translator()


def TextSummarization(Content: str) -> str:
    global HFclient
    count = len(CONFIG['API']['HF']['TOKENs'])
    for _ in range(count):
        try:
            rst = HFclient.summarization(
                input=Content,
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
