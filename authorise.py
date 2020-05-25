import asyncio
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger('authorise')

async def authorise(host,port,token):
    reader, writer = await asyncio.open_connection(
        host,port
    )
    data = await reader.readline()
    logger.info(f'sender:{data}')
    writer.write(token.encode())
    await writer.drain()
    logger.info('token')
    data = await reader.readline()
    logger.info(f'sender:{data}')


if __name__=='__main__':
    load_dotenv()
    host = os.getenv('AUTHORISE_HOST')
    port = os.getenv('AUTHORISE_PORT')
    token = os.getenv('AUTHORISE_TOKEN')
    logging.basicConfig(format=u'%(levelname)-8s %(message)s', level=1, filename='authorise.logs',)

    asyncio.run(authorise(host,port,token))