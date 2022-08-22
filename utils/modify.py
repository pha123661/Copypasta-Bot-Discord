import interactions
from config import CONFIG


class ModifyingCommands(interactions.Extension):
    def __init__(self, client) -> None:
        self.client: interactions.Client = client

    @interactions.extension_command()
    @interactions.option(description="要回覆什麼?")
    async def echo(self, ctx: interactions.CommandContext, text: str):
        await ctx.send(f"bot 說了 {text}!")


def setup(client):
    ModifyingCommands(client)
