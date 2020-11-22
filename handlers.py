from models import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import db_models

class Handler:
    def __init__(self, server_ID, logger):
        self.server_ID = server_ID
        self.server_logger = logger

        engine = create_engine('sqlite:///rssfeed.db', echo=True)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def handle_register_user(self, message):
        if message.name in connected_users:
            self.server_logger.log_error(self.server_ID, f"`{message.name}` is already in use")
            return Message(
                message_type="REGISTER-DENIED", 
                uuid=message.uuid,
                reason=f"`{message.name}` is already in use"
            )
        
        self.server_logger.log_info(self.server_ID, f"Registering new client with name {message.name} at {message.ip}:{message.port}")
        connected_users[message.name] = User(message.name, message.ip, message.port)

        user = db_models.User(message.name, message.ip, message.port, message.password)
        self.session.add(user)
        self.session.commit()

        return Message("REGISTERED", message.uuid)


    def handle_user_update(self, message):
        if message.name not in connected_users:
            self.server_logger.log_error(self.server_ID, f"{message.name} does not exist in the registered users")
            return Message(
                message_type="UPDATE-DENIED", 
                uuid=message.uuid,
                reason=f"`{message.name}` is not a registered user"
            )
        self.server_logger.log_info(self.server_ID, f"Updating info for client {message.name}")
        connected_users[message.name] = User(message.name, message.ip, message.port)

        return  Message(
                message_type="UPDATE-CONFIRMED", 
                uuid=message.uuid, 
                name=message.name, 
                ip=message.ip, 
                port=message.port
            )

    def handle_subjects_update(self, message):
        if message.name not in connected_users:
            self.server_logger.log_error(self.server_ID, f"{message.name} does not exist in the registered users")
            return Message(
                message_type="SUBJECTS-REJECTED", 
                uuid=message.uuid,
                reason=f"`{message.name}` is not a registered user"
            )
        connected_users[message.name].subjects = message.subjects
        self.server_logger.log_info(self.server_ID, f"Updating subjects of user {message.name} to {message.subjects}")
        return Message(
                message_type="SUBJECTS-UPDATED", 
                uuid=message.uuid, 
                name=message.name, 
                subjects=message.subjects
            )

    def handle_publish_message(self, message):
        if message.name not in connected_users:
            self.server_logger.log_error(self.server_ID, f"{message.name} does not exist in the registered users")
            return Message(
                message_type="PUBLISH-DENIED", 
                uuid=message.uuid,
                reason=f"`{message.name}` is not a registered user"
            )
        if message.subject not in connected_users[message.name].subjects:
            self.server_logger.log_error(self.server_ID, f"User {message.name} is not registered to subject {message.subject}")
            return Message(
                message_type="PUBLISH-DENIED", 
                uuid=message.uuid,
                reason=f"User `{message.name}` is not registered to subject {message.subject}"
            )
        self.server_logger.log_info(self.server_ID, f"Publishing message with subject {message.subject}")
        return Message(
            message_type="PUBLISH-CONFIRMED",
            uuid=message.uuid,
        )