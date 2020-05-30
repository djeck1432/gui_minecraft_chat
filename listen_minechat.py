import asyncio
import aiofiles
import datetime
import argparse
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager



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

async def connect_chat(connection,history):
    writer,reader = connection
    while True:
        async with aiofiles.open(history,mode='a') as chat_messages:
            data = await reader.readline()
            message_datetime= datetime.datetime.now().strftime('%d.%m.%y %H:%M')
            await chat_messages.write(f'[{message_datetime}] {data.decode("utf-8")}')


async def main():
    load_dotenv()
    port = os.getenv('CHAT_PORT')
    host = os.getenv('CHAT_HOST')
    history = os.getenv('HISTORY')

    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--chat_host', help='Host', default=host)
    parser.add_argument('--chat_port', help='Port', default=port)
    parser.add_argument('--history', help='path to saved chat messages', default=history)
    args = parser.parse_args()

    async with get_connection(args.chat_host, args.chat_port) as connection:
        connect_chat(connection,args.history)

if __name__=='__main__':
    asyncio.run(main())