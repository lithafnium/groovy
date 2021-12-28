import asyncio 

class MusicQueue(asyncio.Queue):
    async def getdfdfdf(self):
        try:
            await self.get()
            #self.queue.pop(0)
        except Exception as e:
            print(e)

    # async def put(self, item):
    #     try:
    #         await self.put(item)
    #         #self.queue.append(item)
    #     except Exception as e:
    #         print(e)