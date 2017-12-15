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

from transaction import transaction_sv


application = Flask(__name__)

mongo = PyMongo(application)
mongo_server = "localhost"
mongo_port = "27017"
str = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(str)
db = connection.filesystem
servers = db.filesystem_servers
server_transactions = transaction_sv()
AUTH_KEY = "qwerty123456789asdfghjkladitya12"
SERVER_HOST = None
SERVER_PORT = None

# Setting the cache location
cache = Cache('/mycachedir')

def file_upload(file, directory, headers):
    print "\n Uploading file ...\n"
    transaction_sv.uploadT(file, directory, headers)


def decrypt_data(key, hashed_val): #decrypting the key
    decrypted_data = AES.new(key, AES.MODE_ECB).decrypt(base64.b64decode(hashed_val))
    return decrypted_data

def server_instance():
    with application.app_context():
        return db.filesystem_servers.find_one({"host": SERVER_HOST, "port": SERVER_PORT})

def file_delete(file, directory, headers):
    print "\n deleting file ...\n"
    transaction_sv.del_transaction(file, directory, headers)



@application.route('/file_uploader', methods=['POST'])
def file_uploader():
    r_data = request.get_data()
    r_head = request.headers
    file_name_encrypt = r_head['filename']
    dir_encrypt = r_head['directory']
    a_key = r_head['access_key'] #access Key

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


@application.route('/file_delete', methods=['POST'])
def file_delete():
    r_data = request.headers
    r_head = r_data['directory']
    file_name_encrypt = r_data['filename']
    a_key = r_data['access_key']

    period_id = decrypt_data(AUTH_KEY, a_key).strip()
    decrypted_directory = decrypt_data(period_id, r_head)
    decrypted_filename = decrypt_data(period_id, file_name_encrypt)

    hash_key = hashlib.md5()
    hash_key.update(decrypted_directory)

    if not db.directories.find_one(
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]})
    file = db.files.find_one(
        {"name": decrypted_filename, "directory": directory['identifier'], "server": server_instance()["identifier"]})
    if not file:
        print("No file found")
        return jsonify({"success": False})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=file_delete, args=(file['identifier'], directory['identifier'], r_data),
                               kwargs={})
        thr.start()
    return jsonify({'success': True})

@application.route('/file/download', methods=['POST'])
def file_download():
    r_head = request.headers
    encrypted_filename = r_head['filename']
    encrypted_directory = r_head['directory']
    a_key = r_head['access_key']

    period_id = decrypt_data(AUTH_KEY, a_key).strip()
    decrypted_directory = decrypt_data(period_id, encrypted_directory)
    decrypted_filename = decrypt_data(period_id, encrypted_filename)

    hash_key = hashlib.md5()
    hash_key.update(decrypted_directory)

    directory = db.directories.find_one(
        {"name": decrypted_directory, "identifier": hash_key.hexdigest(), "server": server_instance()["identifier"]})
    if not directory:
        return jsonify({"success": False})

    file = db.files.find_one(
        {"name": decrypted_filename, "directory": directory['identifier'], "server": server_instance()["identifier"]})
    if not file:
        return jsonify({"success": False})

    cache_hash = file['identifier'] + "/" + directory['identifier'] + "/" + server_instance()["identifier"]
    if cache.get(cache_hash):
        return cache.get(cache_hash)
    else:
        return flask.send_file(file['identifier'])





if __name__ == '__main__':
    with application.app_context():
        for current_sv in db.filesystem_servers.find():
            print(current_sv)
            if (current_sv['in_use'] == False):
                current_sv['in_use'] = True
                SERVER_PORT = current_sv['port']
                SERVER_HOST = current_sv['host']
                db.filesystem_servers.update({'identifier': current_sv['identifier']}, current_sv, upsert=True)
                application.run(host=current_sv['host'], port=current_sv['port'])


