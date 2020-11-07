import socket
import sys
import json

# TODO: Dont use absolute path
sys.path.insert(1, "D:\Schoolwork\Fall 2020\Coen 445\Project\RSSFeed\models")
from models import Message, ACTION_LIST, User

# Dictionary of names to user objects
connnected_users = {}

# Start the server and listen on host:port
def serve(host, port):
    server_addr = (host, port)
    UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPSock.bind(server_addr)

    buf = 1024  # Message buffer

    try:
        # Listen for incoming messages
        message = Message()
        while True:
            (data, addr) = UDPSock.recvfrom(buf)
            message.json_deserialize(json.loads(data))
            print("Received message: " + json.dumps(message.json_serialize(), indent=4))

            if message.message_type not in ACTION_LIST:
                raise Exception("Undefined message Type")

            if message.message_type == "REGISTER":
                if message.name in connnected_users:
                    print(f"{message.name} is already a registered user, denying registration")
                    send(UDPSock, Message("REGISTER-DENIED", message.uuid, "Name is already in use"), addr)
                else:
                    print(f"Registering new client at {message.ip}:{message.port}")
                    connnected_users[message.name] = User(message.name, message.ip, message.port)
                    send(UDPSock, Message("REGISTERED", message.uuid), addr)
                # TODO: 1) Inform second server
                #       2) Update Db file
            elif message.message_type == "DE-REGISTER":
                connnected_users.pop(message.name, None)
                # TODO: 1) Inform second server
                #       2) Update Db file
            elif message.message_type == "UPDATE":
                if message.name not in connnected_users:
                    print(f"{message.name} does not exist in thee registered users")
                    send(UDPSock, Message("UPDATE-DENIED", message.uuid, "Name does not exist"), addr)
                else:
                    print(f"Updating info for client {messagee.name}")
                    send(UDPSock, Message("UPDATE-CONFIRMED", message.uuid, message.name, message.ip, message.port), addr)
                # TODO: 1) Inform second server
                #       2) Update Db file
               
    except Exception as msg:
        print(msg)
        UDPSock.close()

def send(sock, message, addr):
    try:
        sock.sendto(json.dumps(message.json_serialize()).encode(), addr)
    except socket.error as err:
        print(err)

   
if __name__ == '__main__':
    serve("127.0.0.1", 20001) 
