import socket
import aiofiles
import logging
import gui
import asyncio
import json
import os
import argparse
from dotenv import load_dotenv
import datetime,time
from async_timeout import timeout
from anyio import create_task_group, run
from connection import get_connection
import tkinter


authorization_logger = logging.getLogger('authorization')
watchdog_logger = logging.getLogger('watchdog_logger')


def restart_func(func):
    async def wrappers(*args, **kwargs):
        while True:
            try:
                await func(*args,**kwargs)
            except (asyncio.TimeoutError,socket.gaierror):
                await asyncio.sleep(1)
    return wrappers


async def authorise(reader, writer, hash,
                    watchdog_queue, status_updates_queue):
    data = await reader.readline()
    authorization_logger.info(f'sender:{data}')
    await write_to_server(writer, hash)

    response = await reader.readline()
    token_valid = json.loads(response)
    if token_valid:
        watchdog_queue.put_nowait('Prompt before auth')
        nickname = json.loads(response)['nickname']
        nickname_received = gui.NicknameReceived(nickname)
        status_updates_queue.put_nowait(nickname_received)

        watchdog_queue.put_nowait('Authorization done')
    else:
        raise gui.InvalidToken



async def read_msgs(chat_host, chat_port, messages_queue,
                    status_updates_queue, watchdog_queue):
    try:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
        async with get_connection(chat_host, chat_port) as connection:
            reader, writer = connection
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            while True:
                async with aiofiles.open('chat_messages.txt', mode='a') as chat_messages_file:
                    data = await reader.readline()
                    message_datetime = datetime.datetime.now().strftime('%d.%m.%y %H:%M')
                    message_text = f'[{message_datetime}] {data.decode("utf-8")}'
                    messages_queue.put_nowait(message_text)
                    await chat_messages_file.write(message_text)
                    watchdog_queue.put_nowait('New message in chat')
    finally:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
        raise


async def read_messages_file(filepath, queue):
    if os.path.exists(filepath):
        while True:
            async with aiofiles.open(filepath,mode='r') as chat_messages_file:
                message_text = await chat_messages_file.read()
                queue.put_nowait(message_text)


async def send_msgs(authorization_host, authorization_port, hash,
                    sending_queue, watchdog_queue, status_updates_queue):
    try:
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
        async with get_connection(authorization_host,authorization_port) as connection:
            reader, writer = connection
            await authorise(reader, writer, hash, watchdog_queue, status_updates_queue)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
            while True:
                input_text = await sending_queue.get()
                cleared_input_text = input_text.replace('\n', '')
                await write_to_server(writer,cleared_input_text)

                await reader.readline()
                watchdog_queue.put_nowait('Message sent')
    finally:
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
        raise

async def watch_for_connection(queue):
    while True:
        async with timeout(5) as cm:
            info_log = await queue.get()
            print(f'[{time.time()}] {info_log}')
        if cm.expired:
            print(f'[{time.time()}] 1s timeout is elapsed')
            raise (ConnectionError,asyncio.TimeoutError)

async def write_to_server(writer,text):
    writer.write(f'{text}\n\n'.encode())
    await writer.drain()



@restart_func
async def handle_connection(chat_host,chat_port,
                            messages_queue, sending_queue, status_updates_queue,
                            authorization_host, authorization_port, hash,
                            ):

    watchdog_queue = asyncio.Queue()
    print('start reconnect')
    async with create_task_group() as connection_tg:
        await connection_tg.spawn(read_msgs,
                                chat_host, chat_port, messages_queue,
                                status_updates_queue, watchdog_queue),
        await connection_tg.spawn(send_msgs,authorization_host,authorization_port,hash,
                                          sending_queue, watchdog_queue, status_updates_queue),
        await connection_tg.spawn(watch_for_connection,watchdog_queue),


async def main():
    load_dotenv()
    chat_port = os.getenv('CHAT_PORT')
    chat_host = os.getenv('CHAT_HOST')
    history = os.getenv('HISTORY')

    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--chat_host', help='Host', default=chat_host)
    parser.add_argument('--chat_port', help='Port', default=chat_port)
    parser.add_argument('--history', help='path to saved chat messages', default=history)

    authorization_host = os.getenv('AUTHORIZATION_HOST')
    authorization_port = os.getenv('AUTHORIZATION_PORT')
    hash = os.getenv('AUTHORISE_TOKEN')

    parser.add_argument('--authorization_host', help='Host', default=authorization_host)
    parser.add_argument('--authorization_port', help='Port', default=authorization_port)
    parser.add_argument('--hash', help='enter your hash', default=hash)
    parser.add_argument('--log_path', help='enter path to log file', default='authorise.logs')
    args = parser.parse_args()

    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename='watchdog_log.logs',)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    async with create_task_group() as chat_tg:
        await chat_tg.spawn(handle_connection,args.chat_host,args.chat_port,
                                             messages_queue, sending_queue, status_updates_queue,
                                             args.authorization_host, args.authorization_port, args.hash,)
        await chat_tg.spawn(read_messages_file, args.history, messages_queue)
        await chat_tg.spawn(gui.draw, messages_queue,sending_queue,status_updates_queue)


if __name__=='__main__':
    try:
        run(main)
    except (KeyboardInterrupt,tkinter.TclError):
        print('exit')

