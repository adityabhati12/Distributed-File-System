import json
import requests
import base64
from pymongo import MongoClient
from Crypto.Cipher import AES

mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.filesystem

u_id = "1"
PUB_KEY = "qwerty123456789asdfghjkladitya12"
u_pwd = "dxsabewduwkkjklk"

secret_hash = AES.new(PUB_KEY, AES.MODE_ECB)

headers = {'Content-type': 'application/json'}
payload = {'u_id': u_id
    , 'u_password': u_pwd
    , 'p_key': PUB_KEY}
request = requests.post("http://localhost:5000/user_creation", data=json.dumps(payload), headers=headers)

headers = {'Content-type': 'application/json'}
payload = {'u_id': u_id
    , 'u_password': u_pwd}
request = requests.post("http://localhost:5000/user_login", data=json.dumps(payload), headers=headers)

if (request != None):
    print "\nFile Management Continuation\n"

    server_response = request.text
    print server_response
    encoded_hashed_ticket = json.loads(server_response)["ticket"]
    decoded_hashed_ticked = secret_hash.decrypt(base64.b64decode(encoded_hashed_ticket))
    data = json.loads(decoded_hashed_ticked.strip())

    period_id = data["period_id"]
    sv_host = data["server_host"]
    sv_port = data["server_port"]
    access_key = data["access_key"]
    virtual_structure_hash = AES.new(period_id, AES.MODE_ECB)

    print ""
    print data
    print ""


    directory = "/fileserver/location"
    filename = "test-files/test.txt"
    encrypyted_directory = base64.b64encode(
        virtual_structure_hash.encrypt(directory + b" " * (AES.block_size - len(directory) % AES.block_size)))
    encrypyted_filename = base64.b64encode(
        virtual_structure_hash.encrypt(filename + b" " * (AES.block_size - len(filename) % AES.block_size)))

    data = open('test-files/test.txt', 'rb').read()
    headers = {'access_key': access_key
        , 'directory': encrypyted_directory
        , 'filename': encrypyted_filename}

    request = requests.post("http://" + sv_host + ":" + sv_port + "/file_uploader", data=data, headers=headers)
    print request.text

    request = requests.post("http://" + sv_host + ":" + sv_port + "/file/download", headers=headers)
    print request.text

    request2 = requests.post("http://" + sv_host + ":" + sv_port + "/file_delete", headers=headers)
    print request2.text