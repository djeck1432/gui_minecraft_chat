# Underground chat Minecraft

You can find new cheat codes, and you might have to connect underground chat and chat with other players.

# How to install

Download the repository:
```bash
git clone https://github.com/djeck1432/connect_to_chat
```
Open the folder in the terminal:
```bash
cd connect_to_chat
```
Install requirements libraries and packages:
```bash
pip3 install -r requirements.txt
```

# Setting up the environment:

Setting up the environment you can with through environment variables or `cli`

## Enviroment variables:

### listen_minechat.py

`CHAT_HOST` - host;

`CHAT_PORT` - port;

`HISTORY` - path to the file, where will save a history of the chat;


### authorise.py

`AUTHORIZATION_HOST` - host;

`AUTHORIZATION_PORT` - port;

`AUTHORISE_TOKEN` - your authorisation key for server;


## Setting up with `cli`:

### listen_minechat.py

`--chat_host` - host;

`--chat_port` - port;

`--history` - path to the file, where will save a history of the chat;

### authorise.py

`--authorization_host` - host;

`--authorization_port` - port;

`--hash` - your authorisation key for server;

`--log_path` - path to logs file;


# How to run the code

```bash
python3 listen_minechat.py --chat_host [host] --chat_port [port] --history [path to file] --log_path [name].logs
``` 
 
# How to create new account

In terminal open the next file:
```bash 
python3 registration.py
```
Enter your `nickname` and push the button <i>create account<i>

After that, you can see file `account_data.txt`, where will be your `nickname` and `hash`
