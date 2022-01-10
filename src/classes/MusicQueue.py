import asyncio
from classes.YTDLSource import YTDLSource

class MusicQueue(asyncio.Queue):

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.track_list = []
        self.queue = []
        self.time_loaded = 0

    async def get(self):
        await super().get()
        return self.queue.pop(0)
        self.track_list.pop(0)

    async def put(self, item):
        self.track_list.append(item)
        self.queue.append(item)
        await super().put(item)
        
    async def load(self):
        i = 0
        while (self.time_loaded < 600 and i < len(self.track_list)):
            player = await YTDLSource.from_url(self.track_list[i], loop=self.ctx.bot.loop)
            print(player.title)
            self.queue.append(player)
            await super().put(player)

            self.time_loaded += player.data['duration']
            print(self.time_loaded)
            i += 1

    def enforce_bounds(self):
        if self.queue.size() != super().qsize():
            raise(ValueError('Queue item inconsistency'))