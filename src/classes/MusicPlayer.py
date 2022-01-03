import asyncio
import discord

from Logger import print_log

class MusicPlayer:
    def __init__(self, ctx, bot, start_player=True):
        self.bot = bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue_count = asyncio.Queue()
        self.next = asyncio.Event()
        self.queue = []
        self.track_list = []

        self.np = None  # Now playing message
        self.volume = 0.5
        self.current = None
        self.ctx = ctx
        
        self.start_player = start_player
        self.bot.loop.create_task(self.start_loop())
        self.bot.loop.create_task(self.inactivity_loop())

        self.timer = 0
    
    def set_context(self, ctx):
        self.ctx = ctx
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

    def clear_queue(self):
        self.queue_count = asyncio.Queue()
        self.queue = []

    async def start_loop(self):
        await self.bot.wait_until_ready()
        while True:
            if self.start_player:
                self.ctx.bot.loop.create_task(self.player_loop())
                break

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
            await self.next.wait()
            
    async def inactivity_loop(self):
        await self.bot.wait_until_ready()
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
        # FIXME: this is really stupid but it waits to be connected before going to the next
        while(not self.ctx.voice_client.is_connected()):
            pass
        print_log("Calling next song from queue")
        self.bot.loop.call_soon_threadsafe(self.next.set)
