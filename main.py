import interactions
from config import CONFIG, GuildIDs


def main():
    bot = interactions.Client(
        token=CONFIG['API']['DC']['TOKEN'],
        default_scope=GuildIDs
    )
    bot.load("modify")
    bot.load('interactions.ext.files')
    bot.start()


if __name__ == '__main__':
    main()
