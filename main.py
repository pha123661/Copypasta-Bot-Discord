import interactions
from config import CONFIG, GuildIDs


def main():
    bot = interactions.Client(
        token=CONFIG['API']['DC']['TOKEN'],
        default_scope=GuildIDs
    )
    bot.load("commands_update")
    bot.load("commands_retrieval")
    bot.load("commands_public")
    bot.load('interactions.ext.files')
    bot.start()


if __name__ == '__main__':
    main()
