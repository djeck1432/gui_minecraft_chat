from contextlib import asynccontextmanager
import asyncio


@asynccontextmanager
async def get_connection(authorized_host,authorized_port):
    reader, writer = await asyncio.open_connection(
        authorized_host,authorized_port
    )
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()
