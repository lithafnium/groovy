import asyncio

import discord
import youtube_dl
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
    async def from_url(cls, url, *, loop=None):
        print("loop:", loop)
        loop = loop or asyncio.get_event_loop()
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

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            player = await self.queue.get()
            print("Player:", player)
            self.current = player

            self._guild.voice_client.play(
                player,
                after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set),
            )

            self.np = await self._channel.send("Now playing: {}".format(player.title))
            await self.next.wait()

            print("finsihed waiting")


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

        player = await YTDLSource.from_url(url, loop=self.bot.loop)

        await self.music_player.queue.put(player)

        # await ctx.trigger_typing()
        # if self.guild is None:
        #     self.guild = ctx.guild
        # if self.ctx is None:
        #     self.ctx = ctx

        # await ctx.send("Added {} to queue".format(player.title))

        # await self.queue.put(player)

    # @commands.command()
    # async def play(self, ctx, *, url):
    #     """play from a url (same as yt, but doesn't predownload)"""

    #     player = await YTDLSource.from_url(url, loop=self.bot.loop)
    #     self.queue.append(player)

    #     async def after_song(e):
    #         self.queue.pop(0)

    #         if len(self.queue) == 0:
    #             next_song = self.queue.pop(0)
    #             await play_song(next_song)

    #     async def play_song(player):
    #         async with ctx.typing():
    #             ctx.voice_client.play(
    #                 self.queue[0],
    #                 after=after_song,
    #             )
    #         await ctx.send("Now playing: {}".format(player.title))

    #     if not ctx.voice_client.is_playing():
    #         print("not playing")
    #         await play_song(player)
    #     else:
    #         print("playing")
    #         await ctx.send("Added {} to queue".format(player.title))

    # async with ctx.typing():
    #     ctx.voice_client.play(
    #         self.queue[0],
    #         after=after_song,
    #     )
    # await ctx.send("Now playing: {}".format(player.title))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @commands.command()
    async def q(self, ctx):
        queue_display = " ".join(
            [f"{i+1}. {player.title}\n" for i, player in enumerate(self.queue)]
        )
        queue_display = (
            "Song queue:\n>>> {}".format(queue_display)
            if len(self.queue) > 0
            else "Queue is empty!"
        )
        await ctx.send(queue_display)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description="Relatively simple music bot example",
)


@bot.event
async def on_ready():
    print("Logged in as {0} ({0.id})".format(bot.user))
    print("------")


bot.add_cog(Music(bot))
bot.run("OTI0MzU3ODcxMTc1NjI2Nzgy.YcdZWg.zdrLkbEK5TCxNRqMpFJs4RxWB0o")
