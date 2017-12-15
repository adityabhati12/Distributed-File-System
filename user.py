import base64
import json

import requests
from Crypto.Cipher import AES
from pymongo import MongoClient

mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.filesystem

u_id = "1"
PUB_KEY = "4ThisIsARandomlyGenAESpublicKey4"
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

