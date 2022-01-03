from config import TOKEN
import asyncio
import logging
import discord
import youtube_dl
import pprint
import itertools
from functools import partial

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

pp = pprint.PrettyPrinter(indent=4)

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

ffmpeg_options = {
    "options": "-vn",
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)-15s %(levelname)-8s %(message)s",
        handlers=[
            logging.FileHandler("groovy_bot.log"),
            logging.StreamHandler(),
        ],
    )

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

def print_log(message: str):
    logging.info("[groovybot]: " + str(message))


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
        ytdl.cache.remove()
        to_run = partial(ytdl.extract_info, url=url, download=False)
        data = await loop.run_in_executor(None, to_run)

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"]
        # pp.pprint(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicPlayer:
    def __init__(self, ctx, bot):
        self.bot = bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue_count = asyncio.Queue()
        self.next = asyncio.Event()
        self.queue = []

        self.np = None  # Now playing message
        self.volume = 0.5
        self.current = None
        self.ctx = ctx
        self.bot.loop.create_task(self.player_loop())
    
    def set_context(self, ctx):
        self.ctx = ctx
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

    def clear_queue(self):
        self.queue_count = asyncio.Queue()
        self.queue = []

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next.clear()

            await self.queue_count.get()
            player = self.queue.pop(0)
            self.current = player

            print_log(f"Player: {player}")
            self._guild.voice_client.play(
                player,
                after=self.toggle_next,
            )

            current = discord.Embed(
                title="Now Playing:",
                description=f"**{self.current.title}**",
                color=discord.Color.blue(),
            )
            current.set_thumbnail(url=self.current.data["thumbnail"])
            await self.ctx.send(embed=current)

            print_log(f"Playing {player.title}")
            await self.next.wait()

    def toggle_next(self, e):
        print_log(f"Error: {e}")
        # FIXME: this is really stupid but it waits to be connected before going to the next
        while(not self.ctx.voice_client.is_connected()):
            pass
        print_log("Calling next song from queue")
        self.bot.loop.call_soon_threadsafe(self.next.set)

class Music(commands.Cog):
    def __init__(self, bot):
        self.music_player = None
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            ctx.voice_client.source.volume = 50
            ctx.voice_client.pause()
            await ctx.voice_client.move_to(channel)
            ctx.voice_client.resume()
            return

        await channel.connect()
        print(self.bot.voice_clients)

    @commands.command()
    async def play(self, ctx, *, url):
        await ctx.trigger_typing()

        if self.music_player is None:
            self.music_player = MusicPlayer(ctx, self.bot)
        else:
            self.music_player.set_context(ctx)

        player = await YTDLSource.from_url(url, loop=ctx.bot.loop)

        if ctx.voice_client.is_playing():
            print_log(f"Added {player.title} to queue")
            await ctx.send("Added **{}** to the queue".format(player.title))
        self.music_player.queue.append(player)
        await self.music_player.queue_count.put(0)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                print_log(f"Joining channel {ctx.author.voice.channel}")
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        else:
            if ctx.author.voice and ctx.author.voice.channel != ctx.voice_client.channel:
                self.music_player.clear_queue()
                await ctx.voice_client.disconnect()
                print_log(f"Joining channel {ctx.author.voice.channel}")
                await ctx.author.voice.channel.connect()
                print_log(f"Joined channel {ctx.author.voice.channel}")
                self.music_player.set_context(ctx)

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @commands.command(name="pause", aliases=["p"])
    async def pause(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )
        elif ctx.voice_client.is_paused():
            return

        ctx.voice_client.pause()
        await ctx.send("Paused current song")

    @commands.command(name="resume", aliases=["r"])
    async def resume(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )
        elif not ctx.voice_client.is_paused():
            return

        ctx.voice_client.resume()
        await ctx.send("Resumed the song!")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )

    @commands.command(name="queue", aliases=["q", "playlist"])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(
                "I am not currently connected to voice!", delete_after=20
            )

        if self.music_player is not None:
            current = discord.Embed(
                title="Currently Playing:",
                description=f"**{self.music_player.current.title}**",
                color=discord.Color.blue(),
            )
            current.set_thumbnail(url=self.music_player.current.data["thumbnail"])
            await ctx.send(embed=current)

        player = self.music_player
        if len(player.queue) == 0:
            return await ctx.send("There are currently no more queued songs.")

        # Grab up to 5 entries from the queue...
        upcoming = player.queue[:10]

        fmt = "\n".join(f"**`{i+1}. {_.title}`**" for i, _ in enumerate(upcoming))

        embed = discord.Embed(
            title=f"Upcoming:",
            description=fmt,
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def move(self, ctx, *, url):
        return

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description="Relatively simple music bot example",
)


@bot.event
async def on_ready():
    print("Logged in as {0} ({0.id})".format(bot.user))
    print("------")


bot.add_cog(Music(bot))
#TOKEN = os.getenv('GROOVY_TOKEN')
bot.run(TOKEN)