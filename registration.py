import tkinter as tk
import asyncio
from dotenv import load_dotenv
import os
from anyio import create_task_group, run
import json
from connection import get_connection

class TkAppClosed(Exception):
    pass


async def create_token(reader,writer,text_queue):
    data = await reader.readline()
    nickname = await text_queue.get()

    writer.write('\n'.encode())
    await writer.drain()

    data = await reader.readline()

    writer.write(f'{nickname}\n'.encode())
    await writer.drain()

    data = await reader.readline()
    account_data = json.loads(data)
    account_hash = account_data['account_hash']
    account_nickname = account_data['nickname']
    with open('account_data.txt', 'w') as credentials_file:
        credentials_file.write(f'nickname: {account_nickname}\nhash: {account_hash}')


def clicked(root,txt,text_queue):
    inputed_text = txt.get()
    if inputed_text:
        text_queue.put_nowait(inputed_text)
        nickname_label = tk.Label(root,text=f'Ваш никнейм: {inputed_text}')
        nickname_label.pack()
    else:
        warning_label = tk.Label(root,text=f'Вы ничего не ввели, попробуйте еще раз')
        warning_label.pack()


async def update_tk(root_frame, interval=1 / 120):
    while True:
        try:
            root_frame.update()
        except tk.TclError:
            # if application has been destroyed/closed
            raise TkAppClosed()
        await asyncio.sleep(interval)


async def draw(text_queue):
    root = tk.Tk()
    root.title('Регистрация')
    root.geometry('350x150')

    lbl = tk.Label(root, height=2, text='Введите свой никнейм')
    text_input = tk.Entry(root, width=15)
    btn = tk.Button(root,fg='red', text="создать аккаунт", command=lambda: clicked(root, text_input, text_queue))

    lbl.pack()
    text_input.pack()
    btn.pack()

    await update_tk(root)



async def main():
    load_dotenv()
    authorization_host = os.getenv('AUTHORIZATION_HOST')
    authorization_port = os.getenv('AUTHORIZATION_PORT')

    text_queue = asyncio.Queue()

    async with get_connection(authorization_host,authorization_port) as connection:
        reader, writer = connection
        async with create_task_group() as registration_tg:
            await registration_tg.spawn(create_token, *[reader, writer, text_queue]),
            await registration_tg.spawn(draw,text_queue),


if __name__=='__main__':
    run(main)
