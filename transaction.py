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

cache = Cache('/mycachedir')

def curr_sv(host, port):
    with application.app_context():
        return db.servers.find_one({"host": host, "port": port})

class transaction_sv:
    def uploadT(self, file, dir, headers):

        with application.app_context():
            servers = db.servers.find()
            for server in servers:
                host = server["host"]
                port = server["port"]
                transaction = Transaction(lockT, file, dir)
                transaction.start()

                cache_hash = file + "/" + dir + "/" + server['identifier']
                data = cache.get(cache_hash)
                #printing data

                if curr_sv(host, port)['master_server']:
                    continue

                if (host == sv_host and port == sv_port):
                    continue

                with open(file, "wb") as f:
                    f.write(data)
                print(headers)

                headers = {'access_key': headers['access_key'],
                           'dir': headers['dir'],
                           'filename': headers['filename']}
                r = requests.post("http://" + host + ":" + port + "/file/upload", data=data, headers=headers)

                if r.status_code == sv_response:
                    trans_status.create(file + dir, server, "SUCCESS")
                else:
                    trans_status.create(file + dir, server, "FAILURE")

            if (trans_status.total_success_count()
                    >= trans_status.total_failure_count()
                    + trans_status.total_unknown_count()):
                requests.post("http://" + host + ":" + port + "/file/delete", data='', headers=headers)

