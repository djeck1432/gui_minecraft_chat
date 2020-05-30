import asyncio
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging
import json
import argparse

logger = logging.getLogger('authorise')

async def authorise(connection,hash):
    writer,reader = connection
    data = await reader.readline()
    logger.info(f'sender:{data}')

    writer.write(f'{hash}\n'.encode())
    await writer.drain()

    writer.write('\n'.encode())
    await writer.drain()

    valid_token = await reader.readline()
    token_valid = json.loads(valid_token)

    return token_valid



async def register(connection,nickname):
    writer,reader = connection
    data = await reader.readline()
    logger.info(f'sender:{data}')

    cleaned_nickname = nickname.replace("\n", "")
    writer.write(f'{cleaned_nickname}\n'.encode())
    await writer.drain()

    data = await reader.readline()
    account_data = json.loads(data)
    account_hash = account_data['account_hash']

    return account_hash

async def submit_message(connection,input_text):
    writer,reader = connection
    writer.write(f'{input_text}\n\n'.encode())
    await writer.drain()

    data = await reader.readline()
    logger.info(f'sender:{data}')

@asynccontextmanager
async def get_connection(authorise_host,authorise_port):
    reader, writer = await asyncio.open_connection(
        authorise_host,authorise_port
    )
    try:
        yield writer,reader
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    load_dotenv()
    host = os.getenv('AUTHORISE_HOST')
    port = os.getenv('AUTHORISE_PORT')
    hash = os.getenv('AUTHORISE_TOKEN')

    parser = argparse.ArgumentParser(description='Enviroment setting')
    parser.add_argument('--authorise_host', help='Host',default=host)
    parser.add_argument('--authorise_port', help='Port',default=port)
    parser.add_argument('--hash', help='enter your hash',default=hash)
    parser.add_argument('--log_path', help='enter path to log file', default='authorise.logs' )
    args = parser.parse_args()

    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename=args.log_path, )

    async with get_connection(args.authorise_host, args.authorise_port) as connection:
        token_valid= await authorise(connection, args.hash)
        if not token_valid:
            print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
            nickname = input('Enter your nickname')
            new_hash = await register(connection, nickname)
        while True:
            input_text = input('Type your message: ').replace('\n', '')
            await submit_message(connection,input_text)

    async with get_connection(args.authorise_host, args.authorise_port) as connection:
        await authorise(connection,new_hash)
        while True:

            input_text = input('Type your message: ').replace('\n', '')
            await submit_message(connection, input_text)



if __name__=='__main__':
    asyncio.run(main())
