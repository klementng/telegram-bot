import os
os.chdir(os.path.dirname(__file__))

from core import server
from core import database
from modules.weather import Weather
from modules.shortcuts import Shortcuts,sc


if __name__ == "__main__":
    database.setup("config.json")
    server.setup("config.json",[Weather,Shortcuts,sc])

    server.run()