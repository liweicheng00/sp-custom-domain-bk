import aioredis
import asyncio
from app.config import settings

STOPWORD = "STOP"


class MetadataRedisPool:
    def __init__(self):
        self.r = aioredis.from_url(f'redis://{settings.o2_redis_host}:{settings.o2_redis_port}', db=settings.db_index)
        self.pubsub = self.r.pubsub()
        self.channels = ['channel1']

    async def close(self):
        await self.r.close()

    async def init_redis_data(self):
        print('Init redis metadata.')

    async def publish(self, channel, data):
        print("Publish")
        await self.r.publish(channel, data)

    async def subscribe(self):
        print('Subscribe')
        await self.pubsub.subscribe(*self.channels)
        await self.reader(self.pubsub)

    async def reader(self, pubsub: aioredis.client.PubSub):
        print('start read')
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    print(f"(Reader) Message Received: {message}")

                    if message["data"].decode() == STOPWORD:
                        print("(Reader) STOP")
                        break

                await asyncio.sleep(0.1)
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                await asyncio.sleep(10)
                raise e


