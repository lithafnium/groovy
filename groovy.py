from config import TOKEN
from spotify_client import SpotifyClient

import asyncio

import os

import discord
import youtube_dl
import itertools
from functools import partial

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""


ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_search(cls, url):
        pass

    @classmethod
    async def from_url(cls, url, *, loop):
        print("loop:", loop)
        to_run = partial(ytdl.extract_info, url=url, download=False)
        data = await loop.run_in_executor(None, to_run)

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"]
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicPlayer:
    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = 0.5
        self.current = None
        self.ctx = ctx
        self.ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next.clear()

            player = await self.queue.get()
            self.current = player

            self._guild.voice_client.play(
                player,
                after=self.toggle_next,
            )

            self.np = await self._channel.send("Now playing: {}".format(player.title))
            await self.next.wait()

    def toggle_next(self, e):
        self.ctx.bot.loop.call_soon_threadsafe(self.next.set)


class Music(commands.Cog):
    def __init__(self, bot):
        self.music_player = None
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            ctx.voice_client.source.volume = 50
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
        print(self.bot.voice_clients)

    @commands.command()
    async def play(self, ctx, *, url):
        await ctx.trigger_typing()

        if self.music_player is None:
            self.music_player = MusicPlayer(ctx)

        player = await YTDLSource.from_url(url, loop=ctx.bot.loop)
        await self.music_player.queue.put(player)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @commands.command(name="queue", aliases=["q", "playlist"])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(
                "I am not currently connected to voice!", delete_after=20
            )

        player = self.music_player
        if player.queue.empty():
            return await ctx.send("There are currently no more queued songs.")

        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = "\n".join(f"**`{_.title}`**" for _ in upcoming)
        embed = discord.Embed(title=f"Upcoming - Next {len(upcoming)}", description=fmt)

        await ctx.send(embed=embed)


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("%"),
    description="Relatively simple music bot example",
)


@bot.event
async def on_ready():
    print("Logged in as {0} ({0.id})".format(bot.user))
    print("------")


bot.add_cog(Music(bot))
#TOKEN = os.getenv('GROOVY_TOKEN')
bot.run(TOKEN)