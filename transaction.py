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

    def del_transaction(self, file, dir, headers):

        with application.app_context():
            servers = db.servers.find()
            for server in servers:
                host = server["host"]
                port = server["port"]
                del_transaction = DeleteTransaction(lockT, file, dir, host, port)
                del_transaction.start()

                if curr_sv(host, port)['master_server']:
                    continue

                if (host == sv_host and port == sv_port):
                    continue
                print(headers)
                headers = {'access_key': headers['access_key'],
                           'dir': headers['dir'],
                           'filename': headers['filename']}
                r = requests.post("http://" + host + ":" + port + "/file/delete", data='', headers=headers)

                if r.status_code == sv_response:
                    trans_status.create(file + dir, server, "SUCCESS")
                else:
                    trans_status.create(file + dir, server, "FAILURE")
            if (trans_status.total_success_count()
                    >= trans_status.total_failure_count()
                    + trans_status.total_unknown_count()):
                requests.post("http://" + host + ":" + port + "/file/delete", data='', headers=headers)


class Transaction(threading.Thread):
    def __init__(self, lock, filename, dir):
        threading.Thread.__init__(self)
        self.lock = lock
        self.filename = filename
        self.dir = dir

    def run(self):
        self.lock.acquire()
        return
        self.lock.release()


class DeleteTransaction(threading.Thread):
    def __init__(self, lock, filename, dir, host, port):
        threading.Thread.__init__(self)
        self.lock = lock
        self.filename = filename
        self.dir = dir
        self.host = host
        self.port = port

    def run(self):
        self.lock.acquire()
        if db.files.find_one({"identifier": self.filename, "dir": self.dir,
                              "server": curr_sv(self.host, self.port)}):
            db.files.remove({"identifier": self.filename, "dir": self.dir,
                             "server": curr_sv(self.host, self.port)})
            os.remove(self.filename)
        self.lock.release()


class trans_status:
    def __init__(self):
        pass

    @staticmethod
    def create(name, server, status):
        hash_key = hashlib.md5()
        hash_key.update(name)
        transaction = db.transactions.find_one({"identifier": hash_key.hexdigest()})
        if transaction:
            transaction["ledger"] = status
        else:
            db.transactions.insert(
                {"identifier": hash_key.hexdigest(), "ledger": status, "server-identifier": server['identifier']})

    @staticmethod
    def get(name):
        hash_key = hashlib.md5()
        hash_key.update(name)
        return db.transactions.find_one({"identifier": hash_key.hexdigest()})

    @staticmethod
    def total_success_count():
        count = 0
        for transaction in db.transactions.find():
            if transaction['ledger'] == "SUCCESS":
                count += 1
        return count

    @staticmethod
    def total_failure_count():
        count = 0
        for transaction in db.transactions.find():
            if transaction['ledger'] == "FAILURE":
                count += 1
        return count

    @staticmethod
    def total_unknown_count():
        count = 0
        for transaction in db.transactions.find():
            if transaction['ledger'] == "UNKNOWN":
                count += 1
        return count