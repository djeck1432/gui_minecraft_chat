import asyncio
import os
from dotenv import load_dotenv
import logging
import json

logger = logging.getLogger('authorise')

async def authorise(host,port,hash):
    reader, writer = await asyncio.open_connection(
        host,port
    )

    data = await reader.readline()
    logger.info(f'sender:{data}')

    writer.write(hash.encode('utf-8'))
    await writer.drain()

    writer.write('\n'.encode())
    await writer.drain()

    valid_token = await reader.readline()
    token_valid = valid_token.decode()
    if token_valid:
        print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        new_hash = await register(writer,reader)
        print('new_hasg')
        writer.close()
        await writer.wait_closed()
        reader.close()


    data1 = await reader.readline()
    logger.info(f'sender:{data}\n{data1}')

    while True:
        input_text = input()
        writer.write(f'{input_text}\n\n'.encode('utf-8'))
        await writer.drain()

        data = await reader.readline()
        logger.info(f'sender:{data}')

    writer.close()
    await writer.wait_closed()


async def register(writer,reader):
    data = await reader.readline()
    logger.info(f'sender:{data}')
    print(data.decode())

    nickname = input()
    writer.write(nickname.encode('utf-8'))
    await writer.drain()

    writer.write('\n'.encode('utf-8'))
    await writer.drain()

    data = await reader.readline()
    account_data = json.loads(data)
    account_hash = account_data['account_hash']

    writer.close()
    await writer.wait_closed()

    return account_hash



if __name__=='__main__':
    load_dotenv()
    host = os.getenv('AUTHORISE_HOST')
    port = os.getenv('AUTHORISE_PORT')
    hash = os.getenv('AUTHORISE_TOKEN')
    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename='authorise.logs',)

    asyncio.run(authorise(host,port,hash))