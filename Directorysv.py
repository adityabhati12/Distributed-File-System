import base64
import datetime
import hashlib
import threading

import flask
from Crypto.Cipher import AES
from diskcache import Cache
from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
from pymongo import MongoClient




application = Flask(__name__)

mongo = PyMongo(application)
mongo_server = "localhost"
mongo_port = "27017"
str = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(str)
db = connection.filesystem
servers = db.servers
AUTH_KEY = "17771fab5708b94b42cfd00c444b6eaa"
SERVER_HOST = None
SERVER_PORT = None

# Set the cache location
cache = Cache('/mycachedir')


def decrypt_data(key, hashed_val):
    decrypted_data = AES.new(key, AES.MODE_ECB).decrypt(base64.b64decode(hashed_val))
    return decrypted_data

def server_instance():
    with application.app_context():
        return db.servers.find_one({"host": SERVER_HOST, "port": SERVER_PORT})


@application.route('/file_uploader', methods=['POST'])
def file_uploader():
    r_data = request.get_data()
    r_head = request.r_head
    file_name_encrypt = r_head['filename']
    dir_encrypt = r_head['directory']
    a_key = r_head['a_key'] #access Key

    perdiod_id = decrypt_data(AUTH_KEY, a_key).strip()
    dir_decrypt = decrypt_data(perdiod_id, dir_encrypt)
    fname_decrypt = decrypt_data(perdiod_id, file_name_encrypt)

    h_key = hashlib.md5()
    h_key.update(dir_decrypt)

    if not db.directories.find_one(
            {"name": dir_decrypt, "identifier": h_key.hexdigest(),
             "server": server_instance()["identifier"]}):
        h_key = hashlib.md5()
        h_key.update(dir_decrypt)
        db.directories.insert({"name": dir_decrypt
                                  , "identifier": h_key.hexdigest()
                                  , "server": server_instance()["identifier"]})
        directory = db.directories.find_one(
            {"name": dir_decrypt, "identifier": h_key.hexdigest(),
             "server": server_instance()["identifier"]})
    else:
        directory = db.directories.find_one(
            {"name": dir_decrypt, "identifier": h_key.hexdigest(),
             "server": server_instance()["identifier"]})

    if not db.files.find_one(
            {"name": fname_decrypt, "directory": directory['identifier'],
             "server": server_instance()["identifier"]}):
        h_key = hashlib.md5()
        h_key.update(directory['identifier'] + "/" + directory['name'] + "/" + server_instance()['identifier'])
        db.files.insert({"name": fname_decrypt
                                   , "directory": directory['identifier']
                                   , "server": server_instance()["identifier"]
                                   , "identifier": h_key.hexdigest()
                                   , "updated_at": datetime.datetime.utcnow()})

        file = db.files.find_one({'identifier': h_key.hexdigest()})
        cache_hash = file['identifier'] + "/" + directory['identifier'] + "/" + server_instance()["identifier"]
        cache.set(cache_hash, r_data)
        with open(file['identifier'], "wb") as f:
            f.write(file['identifier'] + "/" + directory['identifier'] + "/" + server_instance()["identifier"])

        file = db.files.find_one(
            {"name": fname_decrypt, "directory": directory['identifier'],
             "server": server_instance()["identifier"]})
    else:
        file = db.files.find_one(
            {"name": fname_decrypt, "directory": directory['identifier'],
             "server": server_instance()["identifier"]})

    print "\nSERVER_HOST = [ " + SERVER_HOST + " ]\n"
    print "\nSERVER_PORT = [ " + SERVER_PORT + " ]\n"
    print server_instance()


    return jsonify({'success': True})
if __name__ == '__main__':
    with application.app_context():
        for current_sv in db.servers.find():
            print(current_sv)
            if (current_sv['in_use'] == False):
                current_sv['in_use'] = True
                SERVER_PORT = current_sv['port']
                SERVER_HOST = current_sv['host']
                db.servers.update({'identifier': current_sv['identifier']}, current_sv, upsert=True)
                application.run(host=current_sv['host'], port=current_sv['port'])


