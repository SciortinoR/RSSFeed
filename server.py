import socket
import errno
import sys
import json
import threading
from logger import Logger
from models import *
import db_models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from handlers import Handler
import win_ctrl_c
win_ctrl_c.install_handler()

class Server:
    def __init__(self, ID, IP, port, other_ID, other_IP, other_port, is_serving=False):
        self.ID = ID
        self.IP = IP
        self.port = port

        self.other_server_ID = other_ID
        self.other_server_IP = other_IP
        self.other_server_port = other_port

        self.is_serving = is_serving

        server_addr = (IP, port)
        self.UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDPSock.bind(server_addr)
        self.UDPSock.setblocking(False)

        self.server_logger = Logger('SERVER')

        db_name = f'sqlite:///server_{ID}.db'
        engine = create_engine(db_name, echo=False, connect_args={'check_same_thread':False})
        Session = sessionmaker(bind=engine)
        self.session = Session()

        self.switching_time_seconds = 300 # Set switching time to 5 minutes by default
        self.timer = threading.Timer(self.switching_time_seconds, self.switch_server)
        if is_serving:
            self.timer.start()

        self.current_server = self.session.query(db_models.Server).filter_by(name=ID).one_or_none()
        self.other_server = self.session.query(db_models.Server).filter_by(name=other_ID).one_or_none()

        if self.other_server:
            self.other_server.ip = other_IP
            self.other_server.port = other_port
        else:
            self.other_server = db_models.Server(name=other_ID, ip=other_IP, port=other_port, active=not is_serving)
            self.session.add(self.other_server)

        if self.current_server:
            self.current_server.ip = IP
            self.current_server.port = port
            self.update_other_server()
        else:
            self.current_server = db_models.Server(name=ID, ip=IP, port=port, active=is_serving)
            self.session.add(self.current_server)

        self.session.commit()

        self.handler = Handler(self.ID, self.server_logger, self.session)

    def update_other_server(self):
        message = Message(
                message_type="UPDATE-SERVER",
                ip=self.IP,
                port=self.port,
                text=self.ID
            )

        self.send(self.UDPSock, message, (self.other_server_IP, self.other_server_port))

    def change_server(self):
        self.is_serving = not self.is_serving
        self.other_server.active = 0 if self.is_serving else 1
        self.session.commit()

    def switch_server(self):
        message = Message(
                message_type="CHANGE-SERVER",
                text=self.ID,
                ip=self.other_server_IP,
                port=self.other_server_port,
            )

        self.change_server()
        self.server_logger.log_info(self.ID, f"Switching to server {self.other_server_ID} at {self.other_server_IP}:{self.other_server_port}")
        self.send(self.UDPSock, message, (self.other_server_IP, self.other_server_port))
        registered_users = self.session.query(db_models.User).all()
        for user in registered_users:
            self.send(self.UDPSock, message, ("127.0.0.1", user.port))

    # Start the server and listen on host:port
    def run_server(self):
        self.server_logger.log_info(self.ID, f"Listening on {self.IP}:{self.port}")
        buf = 1024  # Message buffer

        # TODO: For each message, ensure the expected fields are present
        while True:
            try:
                # Listen for incoming messages
                message = Message()
                
                (data, addr) = self.UDPSock.recvfrom(buf)
                message.json_deserialize(json.loads(data))
                self.server_logger.log_info(self.ID, "Received message: " + json.dumps(message.json_serialize(), indent=4))

                # Messages from the second server are identified by having the other server ID in the `text` field
                sent_from_other_server = message.text == self.other_server_ID

                # Regardless of who the active server is, we must process messages from the other server
                if sent_from_other_server:
                    # A user successfully registered from the other server, we must update this server's database
                    if message.message_type == "REGISTERED":
                        self.handler.handle_register_user(message)

                    elif message.message_type == "UPDATE-SERVER":
                        self.other_server.ip, self.other_server.port = message.ip, message.port
                        self.session.commit()

                    elif message.message_type == "CHANGE-SERVER":
                        print(f"Server {self.ID} being set to active server, switching time set to {self.switching_time_seconds}")
                        self.timer = threading.Timer(self.switching_time_seconds, self.switch_server)
                        self.change_server()
                        self.timer.start()

                    elif message.message_type == "REGISTER-DENIED":
                        self.server_logger.log_error(self.ID, f"Registration of user {message.name} denied.")

                    continue

                # If we aren't the one serving, and the message came from a User, we ignore it
                if not self.is_serving:
                    continue

                if message.message_type == "REGISTER":
                    resp = self.handler.handle_register_user(message)
                    message.text = self.ID
                    message.message_type = resp.message_type

                elif message.message_type == "DE-REGISTER":
                    resp = self.handler.handle_deregister_user(message)
                    # TODO: Notify second server then continue - no more user to respond to
                    if resp:
                        continue

                elif message.message_type in ["UPDATE", "UPDATE-CONFIRMED"]:
                    resp = self.handler.handle_user_update(message)

                    if resp.message_type == "UPDATE-CONFIRMED":
                        message = resp
                    elif resp.message_type == "UPDATE-DENIED":
                        self.send(self.UDPSock, resp, addr)
                        continue
                    
                elif message.message_type in ["SUBJECTS", "SUBJECTS-UPDATED"]: 
                    resp = self.handler.handle_subjects_update(message)

                    if resp.message_type == "SUBJECTS-UPDATED":
                        message = resp
                    elif resp.message_type == "SUBJECTS-REJECTED":
                        self.send(self.UDPSock, resp, addr)
                        continue
                
                elif message.message_type == "PUBLISH": 
                    resp = self.handler.handle_publish_message(message)
                    self.send(self.UDPSock, resp, addr)
                    if resp.message_type == "PUBLISH-CONFIRMED":
                        self.publish_message(self.UDPSock, message.name, message.subject, message.text)
                    continue
                
                else:
                    print(message.message_type)
                    raise Exception("Undefined message Type")
                
                self.send(self.UDPSock, resp, addr)
                self.server_logger.log_info(self.ID, f"Broadcasting message to server {self.other_server_ID}")
                self.send(self.UDPSock, message, (self.other_server_IP, self.other_server_port))

            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    continue

            except Exception as msg:
                print(msg)
                self.UDPSock.close()
        
    # Send text to every connected user which has subject in their list of subjects
    def publish_message(self, sock, sender, subject, text):
        subject = subject.lower()
        for user in self.session.query(db_models.User).filter(db_models.User.subjects.any(name=subject)).filter(db_models.User.name != sender).all():
            self.send(sock, Message("MESSAGE", name=sender, subject=subject, text=text), (user.ip, user.port))

    # Send message to addr using sock
    def send(self, sock, message, addr):
        try:
            sock.sendto(json.dumps(message.json_serialize()).encode(), addr)
        except socket.error as err:
            print(err)

if __name__ == '__main__':
    args = sys.argv[1:]
    print(f"args = {sys.argv[1:]}")
    if len(args) < 7:
        print("Error - invalid argument count")
        print("Expecting: python server.py <server_id> <server_ip> <server_port> <other_server_id> <other_server_ip> <other_server_port> <is_serving>")
        sys.exit()

    name, ip, port, other_name, other_ip, other_port, is_active = args
    Server(ID=name, IP=ip, port=int(port), other_ID=other_name, other_IP=other_ip, other_port=int(other_port), is_serving=is_active.lower() == 'true').run_server()
    
