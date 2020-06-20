from tkinter import *
import asyncio
from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager
from anyio import create_task_group, run
import json


@asynccontextmanager
async def get_connection(authorise_host,authorise_port):
    reader, writer = await asyncio.open_connection(
        authorise_host,authorise_port
    )
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


async def create_token(reader,writer,text_queue):
    print('create_token')
    data = await reader.readline()
    nickname = await text_queue.get()
    print(f'nickname : {nickname}')
    writer.write(nickname.encode())
    await writer.drain()

    data = await reader.readline()
    account_data = json.loads(data)
    account_hash = account_data['account_hash']
    print(account_hash)


def clicked(root,txt,text_queue):
    input_text = txt.get()
    if input_text:
        text_queue.put_nowait(input_text)
        print(f'input_text:{input_text}')
        nickname_label = Label(root,text=f'Ваш никнейм: {input_text}')
        nickname_label.pack()
    else:
        warning_label = Label(root,text=f'Вы ничего не ввели, попробуйте еще раз')
        warning_label.pack()



async def enter_nickname(root,text_queue):
    print('draw')
    lbl = Label(root, height=2, text='response')
    txt = Entry(root, width=20)
    btn = Button(root, text="Введите nickname", command=lambda: clicked(root, txt, text_queue))
    lbl.pack()
    txt.pack()
    btn.pack()


async def draw(text_queue):
    root = Tk()
    root.title('Введите свой никнейм')
    root.geometry('600x350')
    async with create_task_group() as regist:
        await regist.spawn(enter_nickname,*[root,text_queue]),
        # root.mainloop()



async def main():
    load_dotenv()
    authorise_host = os.getenv('AUTHORISE_HOST')
    authorise_port = os.getenv('AUTHORISE_PORT')

    text_queue = asyncio.Queue()

    async with get_connection(authorise_host,authorise_port) as connection:
        reader, writer = connection
        async with create_task_group() as regist:
            await regist.spawn(create_token, *[reader, writer, text_queue]),
            await regist.spawn(draw,text_queue),




if __name__=='__main__':
    run(main)



