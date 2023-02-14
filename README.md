# 複製文機器人

![ICON](https://github.com/pha123661/Hok_tse_bun_dcbot/blob/master/icons/bot%20icon.jpg?raw=true)
<p align="center">
  <span>中文</span> |
  <a href="https://github.com/pha123661/Hok_tse_bun_dcbot/blob/master/README-EN.md">English</a>
</p>

# 這是什麼東西？

一個用於 Discord 的複製文機器人 \
👉[馬上開始使用](https://discord.com/api/oauth2/authorize?client_id=1011172667426095125&permissions=534723951680&scope=applications.commands%20bot)👈 （記得給bot所有權限歐）

# 功能

* 可以自己新增複製文、圖片給機器人存進資料庫 (每個伺服器都有獨立的資料庫)
* 也可以使用公共資料庫，直接查看別人新增的複製文！
* 機器人會用最新科技根據內容生成 摘要(文章) 或描述(圖片) \
  PS: AI 笨笨的 所以是輔助用 用戶還是需要人工給簡短關鍵字
* 在群組聊天的時候 看到相關的字 機器人會自己浮起來貼複製文
* 可以在資料庫裡面進行搜尋
* 還有更多，請邀請 bot 後使用 `/example` 指令來查看

[`#ImageCaptioning`](https://paperswithcode.com/task/image-captioning)\
[`#TextGeneration`](https://paperswithcode.com/task/text-generation)\
[`#TextSummarization`](https://paperswithcode.com/task/text-summarization)

# 使用方法

由於 bot 還在進行開發，請在 Discord 使用 `/example` 來查看使用方法

# 關於隱私

1. 機器人**看得到**你傳了什麼，但是一般聊天時不會儲存任何資訊，bot 是開源的，不信你自己看
2. 唯一會儲存的資訊就是用戶主動新增進資料庫的東西
3. 圖片並不會儲存到資料庫內，只會儲存在 discord 的伺服器，因爲我沒錢、存不下
4. 我對你的隱私沒興趣

## --- 因爲我很懶 下方文件只有英文版 ---

# Deploy

1. Setup ``config.toml`` following section "Config Setup"
2. Setup Environment variables following section "Environment Variable Setup"
3. Run
    ```python
    python main.py
    ```
4. Profit!


# Environment Variable Setup
Environment Variable: ``APIDCTOKEN``
Description: API token for your Discord bot
Default value= ``YOUR_DISCORD_BOT_SECRET``

---

Environment Variable: ``APITGTOKEN``
Description: API token for your telegram bot, this is used to retrieve images uploaded at Telegram
Default value: ``"YOUR_TELEGRAM_API_TOKEN"`` (no this does not work)

---

Environment Variable: ``APIHFTOKENs``
Description: A list of huggingface tokens, bot switchs token whenever it fails (ex: quota exceeded)
Default value= ``["YOUR_HUGGINGFACETOKEN1", "YOUR_HUGGINGFACETOKEN2",]``

---

Environment Variable: ``APIMONGOURI``
Description: URI to connect to your mongodb
Default value= ``"mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]"``

---

Environment Variable: ``DBDB_NAME``
Description: Database name for private database
Default value= ``"Testing-HokTseBunBot-DC"``

---

Environment Variable: ``DBGLOBAL_DB_NAME``
Description: Database name for public database
Default value= ``"Testing-Global"``

---

# Config Setup
The config file, config.toml, is in toml format
## [SETTING]

Setting: ``LOG_FILE``
Description: Name of your log file
Default value: ``"../log.log"``

---

## [API]
### [API.HF]

---

Setting: ``SUM_MODEL``
Description: The desired model to use for summarization, any model which supports summarization in your language should work
Default value = ``"csebuetnlp/mT5_multilingual_XLSum"``
Note: The model should support inference api to work.

---

Setting: ``MT_MODEL``
Description: The desired model to use for translation, any model which supports translation in your language should work
Default value = ``"Helsinki-NLP/opus-mt-en-zh"``
Note: This setting isn't working since the bot uses google translate

---
