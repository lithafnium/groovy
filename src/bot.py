import asyncio
import logging
import discord
import youtube_dl
import pprint
import itertools

from config import GROOVY_TOKEN
from functools import partial
from discord.ext import commands

from classes.Logger import print_log
from classes.YTDLSource import YTDLSource
from classes.MusicPlayer import MusicPlayer

class Music(commands.Cog):
    def __init__(self, bot):
        self.music_player = None
        self.bot = bot

    async def add_track(self, ctx, name, msg):
        player = await YTDLSource.from_url(name, loop=ctx.bot.loop)

        if ctx.voice_client.is_playing() and msg:
            print_log(f"Added {player.title} to queue")
            await ctx.send("Added **{}** to the queue".format(player.title))
        self.music_player.queue.append(player)
        await self.music_player.queue_count.put(0)

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

        await self.add_track(ctx, url, True)

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
    print_log("Logged in as {0} ({0.id})".format(bot.user))
    print_log("------")


bot.add_cog(Music(bot))
#TOKEN = os.getenv('GROOVY_TOKEN')
bot.run(GROOVY_TOKEN)