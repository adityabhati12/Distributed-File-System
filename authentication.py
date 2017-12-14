import base64 #for encoding and decoding
import hashlib
from flask import request
import json
import random
import string
from flask import Flask
from Crypto.Cipher import AES
from flask import jsonify #to get json format of a file
from pymongo import MongoClient #for connecting to mongodb

mongo_server = "localhost"
mongo_port = "27017"
hash_key = hashlib.md5()

connect_str = "mongodb://" + mongo_server + ":" + mongo_port #creating connection with mongodb
connection = MongoClient(connect_str)

req_database = connection.filesystem
req_database.filesystem_users.drop()
req_database.filesystem_servers.drop()
req_database.directories.drop()
req_database.files.drop()
req_database.transactions.drop()

hash_key.update("localhost" + ":" + "9001")
req_database.filesystem_servers.insert(
    {"identifier": hash_key.hexdigest(), "host": "localhost", "port": "9001", "master_server": True, "in_use": False})

hash_key.update("localhost" + ":" + "9002")
req_database.filesystem_servers.insert(
    {"identifier": hash_key.hexdigest(), "host": "localhost", "port": "9002", "master_server": False, "in_use": False})

hash_key.update("localhost" + ":" + "9002")
req_database.filesystem_servers.insert(
    {"identifier": hash_key.hexdigest(), "host": "localhost", "port": "9003", "master_server": False, "in_use": False})

application = Flask(__name__)

app = Flask(__name__)
AUTH_KEY = "qwerty123456789asdfghjkladitya12"

"""
This functions creates the user and stores user details in the database
"""

@app.route('/user_creation', methods=['POST'])
def user_creation():

    r_data = request.get_json(force=True)

    p_key = r_data.get('p_key')
    u_id = r_data.get('u_id')
    u_password = r_data.get('u_password')

    pass_encrypt = base64.b64encode(AES.new(p_key, AES.MODE_ECB).encrypt(u_password))#encoding the password


    period_id = "weewifu12uweed219i332jdnw4rdfweq"

    req_database.filesystem_users.insert(
        {"u_id": u_id, "period_id": period_id, "p_key": p_key,
         "u_password": pass_encrypt}
    )#adding data to the database


    return jsonify({"Msg": "Generated user",
                    "User id": u_id})#returns a json serialisable type



@app.route('/user_login', methods=['POST'])
def u_login():


    req_data = request.get_json(force=True)
    u_password = req_data.get('u_password')
    u_id = req_data.get('u_id')
    u_info = req_database.filesystem_users.find_one({'u_id': u_id})
    pass_encrypt = u_info['u_password']
    p_key = u_info['p_key']

    decrypted_u_password = AES.new(p_key, AES.MODE_ECB).decrypt(base64.b64decode(pass_encrypt)).strip()#decrypt user password

    if decrypted_u_password == u_password:
        period_id = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
        u_info['period_id'] = period_id
        if req_database.filesystem_users.update({'u_id': u_id}, u_info, upsert=True):
            current_u = u_info
        else:
            return jsonify({'success': False})
    else:
        return jsonify({'success': False})
    if current_u:
        period_key_hash = current_u['period_id'] + b" " * (
            AES.block_size - len(current_u['period_id']) % AES.block_size)
        encoded_hashed_perdiod_key = base64.b64encode(AES.new(AUTH_KEY, AES.MODE_ECB).encrypt(period_key_hash))

        ticket = json.dumps(
            {'period_id': current_u['period_id'], 'server_host': "localhost", 'server_port': "9001",
             'access_key': encoded_hashed_perdiod_key})

        ticket_hash = ticket + b" " * (AES.block_size - len(ticket) % AES.block_size)
        hash_ticket = base64.b64encode(
            AES.new(current_u['p_key'], AES.MODE_ECB).encrypt(ticket_hash))

        print "\nUser Authorized Successful\n"
        return jsonify({'success': True, 'ticket': hash_ticket})
    else:
        return jsonify({'success': False})


if __name__ == '__main__':
    app.run()