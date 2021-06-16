import asyncio
import gui
import time


async def generate_msgs(queue):
    while True:
        queue.put_nowait(time.time())
        await asyncio.sleep(1)


async def main():
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    group = await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        generate_msgs(messages_queue),
    )

asyncio.run(main())
