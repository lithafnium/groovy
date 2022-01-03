import asyncio
import discord

from classes.Logger import print_log

class MusicPlayer:
    def __init__(self, ctx):
        self.bot = ctx.bot
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
        self.ctx.bot.loop.create_task(self.player_loop())
        self.ctx.bot.loop.create_task(self.inactivity_loop())

        self.timer = 0

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next.clear()

            await self.queue_count.get()
            player = self.queue.pop(0)
            self.current = player

            self._guild.voice_client.play(
                player,
                after=self.toggle_next,
            )

            current = discord.Embed(
                title="Currently Playing:",
                description=f"**{self.current.title}**",
                color=discord.Color.blue(),
            )
            current.set_thumbnail(url=self.current.data["thumbnail"])
            await self.ctx.send(embed=current)

            print_log(f"Playing {player.title}")
            self.np = await self._channel.send(
                "Now playing: **{}**".format(player.title)
            )
            await self.next.wait()
            
    async def inactivity_loop(self):
        while True:
            try:
                await asyncio.sleep(1)
                self.timer += 1             
                if self.ctx.voice_client.is_playing() or self.ctx.voice_client.is_paused():
                    self.timer = 0
                
                if self.timer == 600:
                    await self.ctx.voice_client.disconnect()

            except Exception as e:
                if self.ctx.voice_client is None:
                    continue
                print(str(e))

    def toggle_next(self, e):
        print_log(f"Error: {e}")
        self.ctx.bot.loop.call_soon_threadsafe(self.next.set)