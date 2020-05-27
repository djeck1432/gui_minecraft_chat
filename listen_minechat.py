import asyncio
import aiofiles
import datetime
import argparse
import os
from dotenv import load_dotenv


async def connetc_chat(host,port,history):

    reader,writer = await asyncio.open_connection(
        host,port
    )
    while True:
        async with aiofiles.open(history,mode='a') as chat_messages:
            data = await reader.readline()
            message_datetime= datetime.datetime.now().strftime('%d.%m.%y %H:%M')
            await chat_messages.write(f'[{message_datetime}] {data.decode()}')


if __name__=='__main__':
    load_dotenv()
    port = os.getenv('CHAT_PORT')
    host = os.getenv('CHAT_HOST')
    history = os.getenv('HISTORY')



    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--chat_host',help='Host')
    parser.add_argument('--chat_port', help='Port')
    parser.add_argument('--history', help='path to saved chat messages')
    args = parser.parse_args()

    if  args.chat_host:
        host = args.chat_host
    if args.chat_port:
        port = args.chat_port
    if args.history:
        history = args.history

    asyncio.run(connetc_chat(host, port, history))