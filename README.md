# Подпольный чат Minecraft

С помощью данного чата, вы сможете узнать новые читы, а также подключиться к подпольному чату и общаться с другими игроками.

# Как установить

Скачать репозиторий:
```bash
git clone https://github.com/djeck1432/connect_to_chat
```
Откройте папку в терминале:
```bash
cd connect_to_chat
```
Установите необходимые библиотеки:
```bash
pip3 install -r requirements.txt
```

# Настройка окружения:
Настроить окружения вы можете с помощью переменных окружения или с помощью 'cli'.

## Переменные окружения:

### listen_minechat.py

`CHAT_HOST` - хост;

`CHAT_PORT` - порт;

`HISTORY` - путь к файлу, где будет сохраняться история чата;

### authorise.py

`AUTHORISE_HOST` - хост;

`AUTHORISE_PORT` - порт;

`AUTHORISE_TOKEN` - ваш ключ авторизации на сервере;

## Настройка окружения с помощью 'cli':

### listen_minechat.py

`--chat_host` - хост;

`--chat_port` - порт;

`--history` - путь к файлу, где будет сохраняться история чата;

### authorise.py

`--authorise_host` - хост;

`--authorise_port` - порт;

`--hash` - ваш ключ авторизации на сервере;

`--log_path` - путь к лог файлам.

# Пример запуска скрипта
```bash
python3 listen_minechat.py --chat_host [host] --chat_port [port] --history [path to file] --log_path [name].logs
``` 
 




