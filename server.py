import socket
import sys
import json
from logger import Logger
from models import *
from handlers import Handler
import win_ctrl_c
win_ctrl_c.install_handler()

class Server:
    def __init__(self, ID, IP, port, is_serving=False):
        self.ID = ID
        self.IP = IP
        self.port = port
        self.is_serving = is_serving

        server_addr = (IP, port)
        self.UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDPSock.bind(server_addr)

        self.server_logger = Logger('SERVER')

        self.handler = Handler(self.ID, self.server_logger)

    # Start the server and listen on host:port
    def run_server(self):
        self.server_logger.log_info(self.ID, f"Listening on {self.IP}:{self.port}")
        buf = 1024  # Message buffer

        # TODO: Read from db file and restore users

        # TODO: For each message, ensure the expected fields are present
        try:
            # Listen for incoming messages
            message = Message()
            while True:
                (data, addr) = self.UDPSock.recvfrom(buf)
                message.json_deserialize(json.loads(data))
                self.server_logger.log_info(self.ID, "Received message: " + json.dumps(message.json_serialize(), indent=4))

                if message.message_type not in ACTION_LIST:
                    raise Exception("Undefined message Type")

                # TODO: 1) Inform second server
                #       2) Update Db file
                if message.message_type == "REGISTER":
                    resp = self.handler.handle_register_user(message)
                    self.send(self.UDPSock, resp, addr) 
                    continue
                
                if message.message_type == "DE-REGISTER":
                    ret = connected_users.pop(message.name, None)
                    if ret is not None:
                        self.server_logger.log_info(self.ID, f"Successfully de-registered user with name {ret}")
                    continue

                # TODO: 1) Inform second server
                #       2) Update Db file
                if message.message_type == "UPDATE":
                    resp = self.handler.handle_user_update(message)
                    self.send(self.UDPSock, resp, addr) 
                    continue
                    
                # TODO: 1) Inform second server
                #       2) Update Db file
                if message.message_type == "SUBJECTS": 
                    resp = self.handler.handle_subjects_update(message)
                    self.send(self.UDPSock, resp, addr)
                    continue
                
                
                if message.message_type == "PUBLISH": 
                    resp = self.handler.handle_publish_message(message)
                    self.send(self.UDPSock, resp, addr)
                    if resp.message_type == "PUBLISH-CONFIRMED":
                        self.publish_message(self.UDPSock, message.subject, message.text)
                    continue

                # TODO: Handle messages from second server
        except Exception as msg:
            print(msg)
            self.UDPSock.close()
        
        # Send text to every connected user which has subject in their list of subjects
    def publish_message(sock, subject, text):
        for name, user in connected_users.items():
            if subject in user.subjects:
                send(sock, Message("MESSAGE", name=name, subject=subject, text=text), (user.ip, user.port))

    # Send message to addr using sock
    def send(self, sock, message, addr):
        try:
            sock.sendto(json.dumps(message.json_serialize()).encode(), addr)
        except socket.error as err:
            print(err)

if __name__ == '__main__':
    server_A = Server(ID="A", IP="127.0.0.1", port=20001, is_serving=True)
    server_B = Server(ID="B", IP="127.0.0.1", port=24523)
    server_A.run_server()
    # server_B.run_server()