import asyncio
import os
from dotenv import load_dotenv
import logging
import json
import argparse

logger = logging.getLogger('authorise')

async def authorise(host,port,hash):
    reader, writer = await asyncio.open_connection(
        host, port
    )

    data = await reader.readline()
    logger.info(f'sender:{data}')

    writer.write(f'{hash}\n'.encode('utf-8'))
    await writer.drain()

    writer.write('\n'.encode('utf-8'))
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

    valid_token,writer,reader = await authorise(args.host,args.port,args.hash)
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
    asyncio.run(main())