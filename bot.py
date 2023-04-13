import hikari
import tanjun
import os

from hikari import GatewayBot
from dotenv import load_dotenv

load_dotenv()


def build_bot() -> GatewayBot:
    bot = hikari.GatewayBot(os.getenv("BOT_KEY"))

    make_client(bot)

    return bot


def make_client(bot: hikari.GatewayBot) -> tanjun.Client:
    client = (
        tanjun.Client.from_gateway_bot(
            bot,
            mention_prefix=True,
            set_global_commands=792948222946443274
        )
    ).add_prefix("!")

    client.load_modules("components.chat_completion")

    return client
