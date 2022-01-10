import asyncio
import discord

from classes.Logger import print_log
from classes.YTDLSource import YTDLSource
from classes.MusicQueue import MusicQueue

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
        self.music_queue = MusicQueue(ctx)

        self.np = None  # Now playing message
        self.is_loop =  False
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
                self.bot.loop.create_task(self.player_loop())
                break

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next.clear()

            if not self.is_loop or self.ctx.voice_client.is_playing():
                player = await self.music_queue.get() 
                self.current = player
            else:
                # loops the last song
                player = await YTDLSource.from_url(self.current.url, loop=self.ctx.bot.loop)
            
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
                if (
                    self.ctx.voice_client.is_playing()
                    or self.ctx.voice_client.is_paused()
                ):
                    self.timer = 0

                if self.timer == 600:
                    await self.ctx.voice_client.disconnect()

            except Exception as e:
                if self.ctx.voice_client is None:
                    continue
                print(str(e))
    
    ### ADD LOOP TO CHECK FOR LOOP

    """
    queue design:

    
    """
    async def add_track(self, name, needs_msg):
        player = await YTDLSource.from_url(name, loop=self.ctx.bot.loop)

        if self.ctx.voice_client.is_playing() and needs_msg:
            print_log(f"Added {player.title} to queue")
            await self.ctx.send("Added **{}** to the queue".format(player.title))

        await self.music_queue.put(player)

    def toggle_next(self, e):
        print_log(f"Error: {e}")

        # FIXME: this is really stupid but it waits to be connected before going to the next
        while not self.ctx.voice_client.is_connected():
            pass
        print_log("Calling next song from queue")
        self.bot.loop.call_soon_threadsafe(self.next.set)
