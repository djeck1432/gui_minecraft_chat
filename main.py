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


authorise_logger = logging.getLogger('authorise')
watchdog_logger = logging.getLogger('watchdog_logger')

@asynccontextmanager
async def get_connection(chat_host,chat_port):
    reader, writer = await asyncio.open_connection(
        chat_host,chat_port
    )
    try:
        yield writer,reader
    finally:
        writer.close()
        await writer.wait_closed()


async def authorise(watchdog_queue,host,port,hash,queue):
    queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    await watchdog_queue.put('Prompt before auth')
    async with get_connection(host,port) as connection:
        writer, reader = connection
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
            queue.put_nowait(nickname_received)
            queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
            await watchdog_queue.put('Authorization done')
        else:
            queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
            raise gui.InvalidToken


async def read_msgs(chat_host, chat_port, messages_queue,status_updates_queue,watchdog_queue):
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    try:
        async with get_connection(chat_host, chat_port) as connection:
            writer, reader = connection
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            while True:
                async with aiofiles.open('chat_messages.txt', mode='a') as chat_messages:
                    data = await reader.readline()
                    message_datetime = datetime.datetime.now().strftime('%d.%m.%y %H:%M')
                    message_text = f'[{message_datetime}] {data.decode("utf-8")}'
                    messages_queue.put_nowait(message_text)
                    await chat_messages.write(message_text)
                    await watchdog_queue.put('New message in chat')
    except BaseException as exc:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
        print(f'read_msgs: {exc}')
        raise

async def saved_messages(filepath,queue):
    while True:
        async with aiofiles.open(filepath,mode='r') as chat_messages:
            message_text = await chat_messages.read()
            queue.put_nowait(message_text)


async def send_msgs(host,port,queue,watchdog_queue):
    async with get_connection(host,port) as connection:
        writer,reader = connection
        while True:
            input_text = await queue.get()
            watchdog_queue.put_nowait('Message sent')
            cleared_input_text = input_text.replace('\n', '')
            writer.write(f'{cleared_input_text}\n\n'.encode())
            await writer.drain()

            data = await reader.readline()
            #authorise_logger.info(f'sender:{data}')

async def watch_for_connection(queue):
    while True:
        try:
            async with timeout(1.5) as cm:
                info_log = await queue.get()
                print(f'[{time.time()}] {info_log}')
        except:
            print(f'[{time.time()}] 1s timeout is elapsed')

async def handle_connection():
    pass

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

    # authorise_logger.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename=args.log_path,)
    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename='watchdog_log.logs',)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    # await watchdog_queue.put(await messages_queue.get())


    try:
        async with create_task_group() as minechat:
            await minechat.spawn(authorise,*[watchdog_queue,args.authorise_host, args.authorise_port, args.hash,status_updates_queue]),
            await minechat.spawn(read_msgs,*[args.chat_host,args.chat_port,messages_queue,status_updates_queue,watchdog_queue]),
            await minechat.spawn(saved_messages,*[history, messages_queue]),
            await minechat.spawn(send_msgs,*[args.authorise_host,args.authorise_port,sending_queue,watchdog_queue]),
            await minechat.spawn(watch_for_connection,watchdog_queue)
            await minechat.spawn(gui.draw,*[messages_queue, sending_queue, status_updates_queue]),
        # await asyncio.gather(
        #     authorise(watchdog_queue,args.authorise_host, args.authorise_port, args.hash,status_updates_queue),
        #     read_msgs(args.chat_host,args.chat_port,messages_queue,status_updates_queue,watchdog_queue),
        #     saved_messages(history, messages_queue),
        #     send_msgs(args.authorise_host,args.authorise_port,sending_queue,watchdog_queue),
        #     watch_for_connection(watchdog_queue),
        #     gui.draw(messages_queue, sending_queue, status_updates_queue),
        # )
    except BaseException as exc:
        print(f'main: {type(exc)}')
        raise



if __name__=='__main__':
    run(main)

