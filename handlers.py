from models import *
from logger import Logger

server_logger = Logger('SERVER')

def handle_register_user(server_ID, message):
    global server_logger

    if message.name in connected_users:
        server_logger.log_error(server_ID, f"`{message.name}` is already in use")
        return Message(
            message_type="REGISTER-DENIED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is already in use"
        )
    
    server_logger.log_info(server_ID, f"Registering new client with name {message.name} at {message.ip}:{message.port}")
    connected_users[message.name] = User(message.name, message.ip, message.port)
    return Message("REGISTERED", message.uuid)


def handle_user_update(server_ID, message):
    global server_logger

    if message.name not in connected_users:
        server_logger.log_error(server_ID, f"{message.name} does not exist in the registered users")
        return Message(
            message_type="UPDATE-DENIED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is not a registered user"
        )
    print(f"Updating info for client {message.name}")
    connected_users[message.name] = User(message.name, message.ip, message.port)
    return  Message(
            message_type="UPDATE-CONFIRMED", 
            uuid=message.uuid, 
            name=message.name, 
            ip=message.ip, 
            port=message.port
        )

def handle_subjects_update(server_ID, message):
    global server_logger

    if message.name not in connected_users:
        server_logger.log_error(server_ID, f"{message.name} does not exist in the registered users")
        return Message(
            message_type="SUBJECTS-REJECTED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is not a registered user"
        )
    connected_users[message.name].subjects = message.subjects
    server_logger.log_info(server_ID, f"Updating subjects of user {message.name} to {message.subjects}")
    return Message(
            message_type="SUBJECTS-UPDATED", 
            uuid=message.uuid, 
            name=message.name, 
            subjects=message.subjects
        )

def handle_publish_message(server_ID, message):
    global server_logger

    if message.name not in connected_users:
        server_logger.log_error(server_ID, f"{message.name} does not exist in the registered users")
        return Message(
            message_type="PUBLISH-DENIED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is not a registered user"
        )
    if message.subject not in connected_users[message.name].subjects:
        server_logger.log_error(server_ID, f"User {message.name} is not registered to subject {message.subject}")
        return Message(
            message_type="PUBLISH-DENIED", 
            uuid=message.uuid,
            reason=f"User `{message.name}` is not registered to subject {message.subject}"
        )
    server_logger.log_info(server_ID, f"Publishing message with subject {message.subject}")
    return Message(
        message_type="PUBLISH-CONFIRMED",
        uuid=message.uuid,
    )