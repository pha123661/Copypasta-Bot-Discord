import interactions
from config import CONFIG, GuildIDs


def main():
    bot = interactions.Client(
        token=CONFIG['API']['DC']['TOKEN'],
        default_scope=GuildIDs
    )
    bot.load("utils.modify")
    bot.start()


if __name__ == '__main__':
    main()
