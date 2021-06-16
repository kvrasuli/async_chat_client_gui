import asyncio
import gui
import time
import logging
import configargparse
from dotenv import load_dotenv

logger = logging.getLogger(__file__)


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

def parse_args():
    load_dotenv()
    parser = configargparse.ArgParser()
    parser.add('--host', help='address of host', env_var='CHAT_HOST')
    parser.add('--rport', help='number of port', env_var='CHAT_PORT_TO_READ')
    parser.add('--wport', help='number of port', env_var='CHAT_PORT_TO_WRITE')
    parser.add('--token', help='chat token', env_var='CHAT_TOKEN')
    parser.add('--nickname', help='your nickname', env_var='CHAT_NICKNAME')
    parser.add('-m', '--message', help='message to send') # , required=True
    parser.add('--log', help='enable logs', action='store_true')
    return parser.parse_args()


if __name__ == '__main__': 
    args = parse_args()  
    logging.basicConfig(format="%(levelname)s sender: %(message)s", level=logging.ERROR)
    if args.log:
        logging.basicConfig(level=logging.DEBUG)
    
    asyncio.run(main()) 
