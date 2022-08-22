from collections import defaultdict


class ChatStatusEntity:
    def __init__(self, GuildID: int, Global: bool = False) -> None:
        self.GuildID: int = GuildID
        self.Global: int = Global


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


ChatStatus = keydefaultdict(ChatStatusEntity)
