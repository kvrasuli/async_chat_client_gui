import asyncio
import aiofiles
import datetime
import ast
import gui
import logging
import configargparse
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from tkinter import messagebox

logger = logging.getLogger(__file__)


@asynccontextmanager
async def open_socket(host, port):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


class InvalidToken(Exception):
    pass


async def save_msgs(filepath, queue):
    while True:
        chat_line = await queue.get()
        async with aiofiles.open(filepath, "a", encoding="utf-8") as file:
            await file.write(f"{chat_line}\n")


async def submit_message(reader, writer, message):
    message = message.replace("\n", "")
    writer.write(f"{message}\n\n".encode())
    await writer.drain()
    logger.debug(f"Sending a message {message}...")
    answer = await reader.readline()
    logger.debug(answer.decode())


async def authorize(reader, writer, token):
    writer.write(f"{token}\n".encode())
    await writer.drain()
    logger.debug(f"{token} has been sent!")
    answer = await reader.readline()
    decoded_answer = answer.decode()
    logger.debug(f"{decoded_answer}")
    answer = await reader.readline()
    decoded_answer = answer.decode()
    logger.debug(f"{answer.decode()}")
    if decoded_answer == "null\n":
        logger.debug("The token isn't valid, check it or register again.")
        raise InvalidToken
    nickname = ast.literal_eval(answer.decode())["nickname"]
    print(f"выполнена авторизация. юзер {nickname}")
    return nickname


async def send_msgs(host, port, token, sending_queue, status_updates_queue):
    try:
        async with open_socket(host, port) as stream:
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
            reader, writer = stream[0], stream[1]
            try:
                nickname = await authorize(reader, writer, token)
                event = gui.NicknameReceived(nickname)
                status_updates_queue.put_nowait(event)
            except InvalidToken:
                messagebox.showerror(
                    "Неверный токен", "Проверьте токен, сервер его не узнал"
                )
                raise
            while True:
                message = await sending_queue.get()
                await submit_message(reader, writer, message)
    except ConnectionError:
        logger.error("Reading error!")
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
        await asyncio.sleep(10)


async def read_msgs(host, port, reading_queue, saving_queue, status_updates_queue, filepath):
    try:
        async with aiofiles.open(filepath, "r", encoding="utf-8") as file:
            history = await file.readlines()
        for line in history:
            reading_queue.put_nowait(line.strip())
    except FileNotFoundError:
        logger.info("First launch.")
    try:
        async with open_socket(host, port) as stream:
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            while True:
                reader, _ = stream[0], stream[1]
                chat_line = await reader.readline()
                decoded_chat_line = chat_line.decode().strip()
                timestamp = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")
                chat_line_with_timestamp = f"[{timestamp}] {decoded_chat_line}"
                reading_queue.put_nowait(chat_line_with_timestamp)
                saving_queue.put_nowait(chat_line_with_timestamp)
    except ConnectionError:
        logger.error("Reading error!")
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
        await asyncio.sleep(10)


async def main(host, rport, wport, token, path):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    saving_queue = asyncio.Queue()
    tasks = [
        asyncio.ensure_future(
            gui.draw(messages_queue, sending_queue, status_updates_queue)
        ),
        asyncio.ensure_future(
            read_msgs(host, rport, messages_queue, saving_queue, status_updates_queue, path)
        ),
        asyncio.ensure_future(save_msgs(path, saving_queue)),
        asyncio.ensure_future(send_msgs(host, wport, token, sending_queue, status_updates_queue)),
    ]
    try:
        await asyncio.gather(*tasks)
    except InvalidToken:
        for task in tasks:
            task.cancel()


def parse_args():
    load_dotenv()
    parser = configargparse.ArgParser()
    parser.add("--host", help="address of host", env_var="CHAT_HOST")
    parser.add("--rport", help="number of port", env_var="CHAT_PORT_TO_READ")
    parser.add("--wport", help="number of port", env_var="CHAT_PORT_TO_WRITE")
    parser.add(
        "--path", help="path to chat history file", env_var="CHAT_HISTORY_FILE_PATH"
    )
    parser.add("--token", help="chat token", env_var="CHAT_TOKEN")
    parser.add("--nickname", help="your nickname", env_var="CHAT_NICKNAME")
    parser.add("-m", "--message", help="message to send")  # , required=True
    parser.add("--log", help="enable logs", action="store_true")
    return parser.parse_args()


if __name__ == '__main__': 
    args = parse_args()  
    logging.basicConfig(format="%(levelname)s sender: %(message)s", level=logging.ERROR)
    if args.log:
        logging.basicConfig(level=logging.DEBUG)
    
    asyncio.run(main(args.host, args.rport, args.wport, args.token, args.path)) 
