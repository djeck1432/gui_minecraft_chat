import socket

import aiofiles
import logging
import gui
import asyncio
import json
import os
import argparse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import datetime,time
from async_timeout import timeout
from anyio import sleep, create_task_group, run
import tkinter


authorise_logger = logging.getLogger('authorise')
watchdog_logger = logging.getLogger('watchdog_logger')

# async def check_conection(chat_host,chat_port):
#
#     async with get_connection(chat_host,chat_port) as valid_connection:
#         reader, writer = valid_connection
#         while True:
#             try:
#                 async with timeout(4) as response_delay:
#                         writer.write(''.encode())
#                         await writer.drain()
#                         empty_response = await reader.read()
#             except ConnectionError:
#                 raise




def reconnect(func): #FIXME

    async def wrappers(*args, **kwargs):
        chat_host,chat_port, *_ = args
        while True:
            # try:
                await func(*args)
                print('reconnect')
            # except asyncio.TimeoutError:
                await asyncio.sleep(1)

    return wrappers


@asynccontextmanager
async def get_connection(chat_host,chat_port):
    reader, writer = await asyncio.open_connection(
        chat_host,chat_port
    )
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


async def authorise(reader, writer, hash,
                    watchdog_queue, status_updates_queue):
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    watchdog_queue.put_nowait('Prompt before auth')

    data = await reader.readline()
    authorise_logger.info(f'sender:{data}')
    writer.write(f'{hash}\n'.encode())
    await writer.drain()

    writer.write('\n'.encode())
    await writer.drain()
    response = await reader.readline()
    token_valid = json.loads(response)
    if token_valid:
        nickname = json.loads(response)['nickname']
        print(f'Выполнена авторизация. Пользователь {nickname}.')
        nickname_received = gui.NicknameReceived(nickname)
        status_updates_queue.put_nowait(nickname_received)
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
        watchdog_queue.put_nowait('Authorization done')
    else:
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
        raise gui.InvalidToken


async def read_msgs(chat_host, chat_port, messages_queue,
                    status_updates_queue, watchdog_queue):
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    try:
        async with get_connection(chat_host, chat_port) as connection:
            reader, writer = connection
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            while True:
                async with aiofiles.open('chat_messages.txt', mode='a') as chat_messages:
                    data = await reader.readline()
                    message_datetime = datetime.datetime.now().strftime('%d.%m.%y %H:%M')
                    message_text = f'[{message_datetime}] {data.decode("utf-8")}'
                    messages_queue.put_nowait(message_text)
                    await chat_messages.write(message_text)
                    watchdog_queue.put_nowait('New message in chat')
    except BaseException:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
        raise


async def save_messages(filepath,queue):
    while True:
        async with aiofiles.open(filepath,mode='r') as chat_messages:
            message_text = await chat_messages.read()
            queue.put_nowait(message_text)


async def send_msgs(authorise_host, authorise_port, hash,
                    sending_queue, watchdog_queue, status_updates_queue):
    async with get_connection(authorise_host,authorise_port) as connection:
        reader, writer = connection
        await authorise(reader, writer, hash, watchdog_queue, status_updates_queue)
        while True:
            input_text = await sending_queue.get()
            watchdog_queue.put_nowait('Message sent')
            cleared_input_text = input_text.replace('\n', '')
            writer.write(f'{cleared_input_text}\n\n'.encode())
            await writer.drain()

            await reader.readline()


async def watch_for_connection(queue,status_updates_queue):
    try:
        while True:
            async with timeout(5) as cm:
                info_log = await queue.get()
                print(f'[{time.time()}] {info_log}')
            if cm.expired:
                status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
                print(f'[{time.time()}] 1s timeout is elapsed')
    except ConnectionError:
        raise


@reconnect
async def handle_connection(chat_host,chat_port,
                            messages_queue, sending_queue, status_updates_queue,
                            authorise_host, authorise_port, hash,
                            ):

    watchdog_queue = asyncio.Queue()
    try:
        async with create_task_group() as minechat:
            await minechat.spawn(read_msgs,
                                 *[chat_host, chat_port, messages_queue,
                                   status_updates_queue, watchdog_queue]),
            await minechat.spawn(send_msgs, *[authorise_host,authorise_port,hash,
                                              sending_queue, watchdog_queue, status_updates_queue]),
            await minechat.spawn(watch_for_connection, *[watchdog_queue,status_updates_queue]),
            #await minechat.spawn(check_conection,*[chat_host,chat_port]),

    except (asyncio.TimeoutError,socket.gaierror):
         print('start reconnect')


async def main():
    load_dotenv()
    chat_port = os.getenv('CHAT_PORT')
    chat_host = os.getenv('CHAT_HOST')
    history = os.getenv('HISTORY')

    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--chat_host', help='Host', default=chat_host)
    parser.add_argument('--chat_port', help='Port', default=chat_port)
    parser.add_argument('--history', help='path to saved chat messages', default=history)

    authorise_host = os.getenv('AUTHORISE_HOST')
    authorise_port = os.getenv('AUTHORISE_PORT')
    hash = os.getenv('AUTHORISE_TOKEN')

    parser.add_argument('--authorise_host', help='Host', default=authorise_host)
    parser.add_argument('--authorise_port', help='Port', default=authorise_port)
    parser.add_argument('--hash', help='enter your hash', default=hash)
    parser.add_argument('--log_path', help='enter path to log file', default='authorise.logs')
    args = parser.parse_args()

    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename='watchdog_log.logs',)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    async with create_task_group() as chat:
        await chat.spawn(handle_connection,*[args.chat_host,args.chat_port,
                                             messages_queue, sending_queue, status_updates_queue,
                                            args.authorise_host, args.authorise_port, args.hash,])
        await chat.spawn(save_messages, *[args.history, messages_queue])
        await chat.spawn(gui.draw, *[messages_queue,sending_queue,status_updates_queue])


if __name__=='__main__':
    try:
        run(main)
    except (KeyboardInterrupt,tkinter.TclError):
        print('exit')
