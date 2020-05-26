import asyncio
import os
from dotenv import load_dotenv
import logging
import json

logger = logging.getLogger('authorise')

async def authorise(host,port,hash):
    reader, writer = await asyncio.open_connection(
        host, port
    )

    data = await reader.readline()
    logger.info(f'sender:{data}')

    writer.write(f'{hash}\n'.encode('utf-8'))
    await writer.drain()

    writer.write('\n'.encode())
    await writer.drain()

    valid_token = await reader.readline()
    return valid_token,writer,reader



async def register(writer,reader):
    data = await reader.readline()
    logger.info(f'sender:{data}')
    print(data.decode())

    nickname = input().encode("unicode_escape").decode("utf-8")
    writer.write(f'{nickname}\n'.encode('utf-8'))
    await writer.drain()

    data = await reader.readline()
    account_data = json.loads(data)
    account_hash = account_data['account_hash']

    writer.close()
    await writer.wait_closed()

    return account_hash

async def submit_message(writer,reader):
    input_text = input().encode("unicode_escape").decode("utf-8")
    writer.write(f'{input_text}\n\n'.encode('utf-8'))
    await writer.drain()

    data = await reader.readline()
    logger.info(f'sender:{data}')


async def main(host,port,hash):
    valid_token,writer,reader = await authorise(host,port,hash)
    token_valid = json.loads(valid_token)
    if not token_valid:
        print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        new_hash = await register(writer,reader)
        writer.close()
        await writer.wait_closed()

        _,writer,reader = await authorise(host,port,new_hash)

    print('Type your message:')
    while True:
        await submit_message(writer,reader)


if __name__=='__main__':
    load_dotenv()
    host = os.getenv('AUTHORISE_HOST')
    port = os.getenv('AUTHORISE_PORT')
    hash = os.getenv('AUTHORISE_TOKEN')
    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename='authorise.logs',)

    asyncio.run(main(host,port,hash))