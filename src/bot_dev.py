from config import GROOVY_TOKEN
from clients.SpotifyClient import SpotifyClient

import asyncio
import discord
from discord.ext import commands

from classes.Logger import print_log
from classes.YTDLSource import YTDLSource
from classes.MusicPlayer import MusicPlayer


class Music(commands.Cog):
    def __init__(self, bot):
        self.music_player = None
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            ctx.voice_client.source.volume = 35
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
        print(self.bot.voice_clients)

    @commands.command(anme='play', aliases=['p'])
    async def play(self, ctx, *, url):
        await ctx.trigger_typing()
        if self.music_player is None:
            self.music_player = MusicPlayer(ctx)

        if 'https://open.spotify.com/playlist/' in url:
            url = url.removesuffix('https://open.spotify.com/playlist/')
            url = url.split('?')
            sp_id = url[0]

            sp = SpotifyClient()
            playlist = sp.get_playlist(sp_id)
            
            for track in playlist:
                await self.add_track(ctx, track + 'audio', False)

        if 'https://open.spotify.com/track/' in url:
            url = url.removesuffix('https://open.spotify.com/track/')
            url = url.split('?')
            sp_id = url[0]

            sp = SpotifyClient()
            track = sp.get_track(sp_id)

            await self.add_track(ctx, track + 'audio', True)

        else:
            await self.add_track(ctx, url, True)

    async def add_track(self, ctx, name, msg):
        player = await YTDLSource.from_url(name, loop=ctx.bot.loop)

        if ctx.voice_client.is_playing() and msg:
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

        # set timer here to avoid disconnecting with time overlap
        if self.music_player is not None:
            self.music_player.timer = 0

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @commands.command()
    async def pause(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )
        elif ctx.voice_client.is_paused():
            return

        ctx.voice_client.pause()

        await ctx.send("Paused current song")

    @commands.command()
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

    @commands.command(aliases=['m'])
    async def move(self, ctx, input):
        try:
            # indices should be 1 start
            indices = input.slice(" ")
            indices = list(map(int, indices))

            if len(indices) == 2:
                start = indices[0]
                end = indices[1]
                player = self.music_player.queue.pop(start - 1)
                self.music_player.queue.insert(end - 1, player)
            else:
                ctx.channel.send(
                    'Invalid input'
                )

        except Exception as e:
            ctx.channel.send(
                'Invalid input'
            )
            print(str(e))

    @commands.command(aliases=['b'])
    async def bump(self, ctx, target):
        return

    @commands.command(aliases=['c'])
    async def clear(self, ctx):
        self.music_player.queue_count = asyncio.Queue()
        self.music_player.queue = []

    @commands.command(aliases=['d'])
    async def delete(self, ctx, target):
        try:
            # index is 1 based
            index = int(target)
            await self.music_player.queue_count.get()
            self.music_player.queue.pop(index - 1)
        except Exception as e:
            ctx.channel.send(
                'Invalid input'
            )
            print(str(e))

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
bot.run(GROOVY_TOKEN)