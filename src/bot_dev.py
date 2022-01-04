from config import GROOVY_TOKEN
from clients.SpotifyClient import SpotifyClient

import asyncio
import discord
from discord.ext import commands

from classes.Logger import print_log
from classes.YTDLSource import YTDLSource
from classes.MusicPlayer import MusicPlayer


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description="Relatively simple music bot example",
)

bot.music_player = None


bot.load_extension("cogs.music")
bot.load_extension("cogs.queue")


@bot.event
async def on_ready():
    print_log("Logged in as {0} ({0.id})".format(bot.user))
    print_log("------")


# TOKEN = os.getenv('GROOVY_TOKEN')
bot.run(GROOVY_TOKEN)
