![ICON](https://github.com/pha123661/Hok_tse_bun_dcbot/blob/master/icons/bot%20icon.jpg?raw=true)
<p align="center">
  <a href="www.google.com">中文</a> |
  <span>English</span>
</p>

# What Is This?
A "Ho̍k tsè bûn" / "copypasta" / "複製文" bot for Discord \
👉[Start using the bot](https://discord.com/api/oauth2/authorize?client_id=1011172667426095125&permissions=534723951680&scope=applications.commands%20bot)👈, please authorize the bot to be granted all necessary permissions that it has requested.

# Features
* Post related copypasta for you whenever the bot detects matching keyword
* Generate summarization (or caption, for media) automaticly by utlizing top-of-the-line DL models
  * Model used for text summarization: [csebuetnlp/mT5_multilingual_XLSum](https://huggingface.co/csebuetnlp/mT5_multilingual_XLSum)
  * Model used for image captioning: [OFA-Sys/OFA-base](https://huggingface.co/OFA-Sys/OFA-base)
* Provides a cross-platform, public database shared among all users
* and more......

[`#ImageCaptioning`](https://paperswithcode.com/task/image-captioning) \
[`#TextGeneration`](https://paperswithcode.com/task/text-generation) \
[`#TextSummarization`](https://paperswithcode.com/task/text-summarization)

# Usage
Currently in development mode, the usage document is only maintained at bots ``/example`` command

# Deploy
1. Setup ``config.toml`` following section "Config Setup"
2. Setup Environment variables following section "Environment Variable Setup"
3. Run
    ```python
    python main.py
    ```
4. Profit!


# Environment Variable Setup
Environment Variable: ``APIDCTOKEN``\
Description: API token for your Discord bot\
Default value= ``YOUR_DISCORD_BOT_SECRET``

---

Environment Variable: ``APITGTOKEN``\
Description: API token for your telegram bot, this is used to retrieve images uploaded at Telegram\
Default value: ``"YOUR_TELEGRAM_API_TOKEN"`` (no this does not work)

---

Environment Variable: ``APIHFTOKENs``\
Description: A list of huggingface tokens, bot switchs token whenever it fails (ex: quota exceeded)\
Default value= ``["YOUR_HUGGINGFACETOKEN1", "YOUR_HUGGINGFACETOKEN2",]``

---

Environment Variable: ``APIMONGOURI``\
Description: URI to connect to your mongodb\
Default value= ``"mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]"``

---

Environment Variable: ``DBDB_NAME``\
Description: Database name for private database\
Default value= ``"Testing-HokTseBunBot-DC"``

---

Environment Variable: ``DBGLOBAL_DB_NAME``\
Description: Database name for public database\
Default value= ``"Testing-Global"``

---

# Config Setup
The config file, config.toml, is in toml format
## [SETTING]

Setting: ``LOG_FILE``\
Description: Name of your log file\
Default value: ``"../log.log"``

---

## [API]
### [API.HF]

---

Setting: ``SUM_MODEL``\
Description: The desired model to use for summarization, any model which supports summarization in your language should work\
Default value = ``"csebuetnlp/mT5_multilingual_XLSum"``
Note: The model should support inference api to work.

---

Setting: ``MT_MODEL``\
Description: The desired model to use for translation, any model which supports translation in your language should work\
Default value = ``"Helsinki-NLP/opus-mt-en-zh"``
Note: This setting isn't working since the bot uses google translate

---
