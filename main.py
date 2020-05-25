import asyncio
import aiofiles
import datetime
import argparse


async def connetc_server():

    reader,writer = await asyncio.open_connection(
        'minechat.dvmn.org',5000
    )
    while True:
        async with aiofiles.open('chat_messages.txt',mode='a') as chat_messages:
            data = await reader.readline()
            message_datetime= datetime.datetime.now().strftime('%d.%m.%y %H:%M')
            await chat_messages.write(f'[{message_datetime}] {data.decode()}')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--host',help='Host')
    parser.add_argument('--port', help='Port')
    parser.add_argument('--history', help='path to saved chat messages')
    args = parser.parse_args()


    asyncio.run(connetc_server())