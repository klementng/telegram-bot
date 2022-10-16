# Telegram Bot

A simple HTTPs telegram bot application built with python 

## Setup

Use pip to install the required packages
```bash
pip install -r requirements.txt
```

Configure the config.json file with the path to a self-signed certificate / private key, telegram API token, host. port, etc.

```json
{
    "server": {
        "HOST": "0.0.0.0",
        "HOSTNAME": "www.example.com",
        "PORT": 88,
        "CA_CERT_PATH": null,
        "CERT_PATH": "/path/to/certificate.pem",
        "KEY_PATH": "path/to/key.pem",
        "BOT_TOKEN": "123ABC"
    },
    "database":{
        "DB_PATH":"core/users.db"
    }
}
```

## Usage

Running the server

```bash
cd telegram_bot/
python main.py
```

## Features

The bot currently has 2 modules:

### 1. Singapore Weather

This modules fetches latest weather forecast using weather api provided by the sinagpore government at: https://data.gov.sg/dataset/weather-forecast

**Available Commands:**

1) Show inline options:
``` 
/weather
```
2) Get weather forecast for the next 24hours:
    
```
/weather forecast24 [north/south/east/west/central]
```
3) Get Weather forecast for the next 4 day
``` 
/weather forecast4d
```
4) Show satelite map of current rainareas
``` 
/weather rainmap
```
### 2. Shortcuts
This modules allow users to save favourite commands to send to the bot.

**Available Commands for /shortcuts**

1) Inline options:
```    
/shortcuts
```
2) Show list of saved shortcut and clickable inline buttons in telegram
``` 
/shortcuts show
```
3) Modify the shortcut list
``` 
/shortcuts modify
```


