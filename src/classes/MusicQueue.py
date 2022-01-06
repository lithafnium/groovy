import asyncio

class MusicQueue(asyncio.Queue):

    def __init__(self):
        self.track_list = []
        self.queue = []

    async def get(self):
        await super().get()
        self.queue.pop(0)
        #self.track_list.pop(0)

    async def put(self, item):
        self.queue.append(item)
        await super().put(item)

    async def load(self):
        return