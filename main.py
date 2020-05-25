import asyncio
import aiofiles
import datetime
import argparse
import os
from dotenv import load_dotenv

async def connetc_server(port,host,history):

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
    port = os.getenv('PORT')
    host = os.getenv('HOST')
    history = os.getenv('HISTORY')

    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--host',help='Host')
    parser.add_argument('--port', help='Port')
    parser.add_argument('--history', help='path to saved chat messages')
    args = parser.parse_args()


    asyncio.run(connetc_server(port,host,history))