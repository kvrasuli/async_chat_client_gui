import asyncio
import gui
import logging
import configargparse
from dotenv import load_dotenv
from contextlib import asynccontextmanager

logger = logging.getLogger(__file__)


@asynccontextmanager
async def open_socket(host, port): 
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


async def read_msgs(host, port, queue):
    try:
        async with open_socket(host, port) as stream:
            while True:
                reader, _ = stream[0], stream[1]
                chat_line = await reader.readline()
                queue.put_nowait(chat_line.decode().strip())
    except ConnectionError:
        logger.error('Reading error!')
        await asyncio.sleep(10)


async def main(host, rport, wport):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    group = await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(host, rport, messages_queue),
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
    
    asyncio.run(main(args.host, args.rport, args.wport)) 
