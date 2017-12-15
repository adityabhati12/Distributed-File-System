import hashlib
import os
import threading

import requests
from diskcache import Cache
from flask import Flask
from flask_pymongo import PyMongo
from pymongo import MongoClient

lockT = threading.Lock()
sv_response = 200
application = Flask(__name__)
mongo = PyMongo(application)
mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.filesystem
AUTH_KEY = "qwerty123456789asdfghjkladitya12"
sv_host = None
sv_port = None