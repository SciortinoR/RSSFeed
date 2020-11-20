import socket
import sys
import json
from handlers import *
import asyncio
from models import *

db_file_path = ""

# Start the server and listen on host:port
def serve(host, port):
    server_addr = (host, port)
    UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPSock.bind(server_addr)

    print(f"Server listening on {host}:{port}")
    buf = 1024  # Message buffer

    # TODO: Read from db file and restore users

    # TODO: For each message, ensure the expected fields are present
    try:
        # Listen for incoming messages
        message = Message()
        while True:
            (data, addr) = UDPSock.recvfrom(buf)
            message.json_deserialize(json.loads(data))
            print("Received message: " + json.dumps(message.json_serialize(), indent=4))

            if message.message_type not in ACTION_LIST:
                raise Exception("Undefined message Type")

            # TODO: 1) Inform second server
            #       2) Update Db file
            if message.message_type == "REGISTER":
                resp = handle_register_user(message)
                send(UDPSock, resp, addr) 
                continue
            
            if message.message_type == "DE-REGISTER":
                ret = connnected_users.pop(message.name, None)
                if ret is not None:
                    printf(f"Successfully de-registered user with name {ret}")
                continue

            # TODO: 1) Inform second server
            #       2) Update Db file
            if message.message_type == "UPDATE":
                resp = handle_user_update(message)
                send(UDPSock, resp, addr) 
                continue
                
            # TODO: 1) Inform second server
            #       2) Update Db file
            if message.message_type == "SUBJECTS": 
                resp = handle_subjects_update(message)
                send(UDPSock, resp, addr)
                continue
            
            
            if message.message_type == "PUBLISH": 
                resp = handle_publish_message(message)
                send(UDPSock, resp, addr)
                if resp.message_type == "PUBLISH-CONFIRMED":
                    publish_message(UDPSock, message.subject, message.text)
                continue

            # TODO: Handle messages from second server
    except Exception as msg:
        print(msg)
        UDPSock.close()

# Send text to every connected user which has subject in their list of subjects
def publish_message(sock, subject, text):
    for name, user in connected_users.items():
        if subject in user.subjects:
            send(sock, Message("MESSAGE", name=name, subject=subject, text=text), (user.ip, user.port))

# Send message to addr using sock
def send(sock, message, addr):
    try:
        sock.sendto(json.dumps(message.json_serialize()).encode(), addr)
    except socket.error as err:
        print(err)

# Set the database file used by this server
def set_db(file):
    global db_file_path
    db_file_path = file
   
# 
def write_to_db():
    pass

if __name__ == '__main__':
    set_db("./database/db.txt")
    serve("127.0.0.1", 20001) 
