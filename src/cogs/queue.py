from config import GROOVY_TOKEN
from clients.SpotifyClient import SpotifyClient

import discord
from discord.ext import commands

from classes.Logger import print_log
from classes.YTDLSource import YTDLSource
from classes.MusicPlayer import MusicPlayer


class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="queue", aliases=["q", "playlist"])
    async def queue_info(self, ctx, url=""):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(
                "I am not currently connected to voice!", delete_after=20
            )

        if self.bot.music_player is not None:
            current = discord.Embed(
                title="Currently Playing:",
                description=f"**{self.bot.music_player.current.title}**",
                color=discord.Color.blue(),
            )
            current.set_thumbnail(url=self.bot.music_player.current.data["thumbnail"])
            await ctx.send(embed=current)

        player = self.bot.music_player
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

    @commands.command(aliases=["m"])
    async def move(self, ctx, input):
        try:
            # indices should be 1 start
            indices = input.slice(" ")
            indices = list(map(int, indices))

            if len(indices) == 2:
                start = indices[0]
                end = indices[1]
                player = self.bot.music_player.queue.pop(start - 1)
                self.bot.music_player.queue.insert(end - 1, player)
            else:
                ctx.channel.send("Invalid input")

        except Exception as e:
            ctx.channel.send("Invalid input")
            print(str(e))

    @commands.command(aliases=["b"])
    async def bump(self, ctx, target):
        return

    @commands.command(aliases=["c"])
    async def clear(self, ctx):
        self.bot.music_player.clear_queue()

    @commands.command(aliases=["d"])
    async def delete(self, ctx, target):
        try:
            # index is 1 based
            index = int(target)
            await self.bot.music_player.queue_count.get()
            self.bot.music_player.queue.pop(index - 1)
        except Exception as e:
            ctx.channel.send("Invalid input")
            print(str(e))


def setup(bot):
    bot.add_cog(Queue(bot))
