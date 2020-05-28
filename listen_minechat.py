import asyncio
import aiofiles
import datetime
import argparse
import os
from dotenv import load_dotenv


async def connect_chat(host, port, history):

    reader,writer = await asyncio.open_connection(
        host,port
    )

    while True:
        try:
            async with aiofiles.open(history,mode='a') as chat_messages:
                data = await reader.readline()
                message_datetime= datetime.datetime.now().strftime('%d.%m.%y %H:%M')
                await chat_messages.write(f'[{message_datetime}] {data.decode("utf-8")}')
        finally:
            writer.close()


if __name__=='__main__':
    load_dotenv()
    port = os.getenv('CHAT_PORT')
    host = os.getenv('CHAT_HOST')
    history = os.getenv('HISTORY')



    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--chat_host',help='Host',default=host)
    parser.add_argument('--chat_port', help='Port',default=port)
    parser.add_argument('--history', help='path to saved chat messages',default=history)
    args = parser.parse_args()

    asyncio.run(connect_chat(args.host, args.port, args.history))