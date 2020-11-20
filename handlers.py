from models import *

def handle_register_user(message):
    if message.name in connected_users:
        print(f"`{message.name}` is already in use")
        return Message(
            message_type="REGISTER-DENIED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is already in use"
        )
    
    print(f"Registering new client with name {message.name} at {message.ip}:{message.port}")
    connected_users[message.name] = User(message.name, message.ip, message.port)
    return Message("REGISTERED", message.uuid)


def handle_user_update(message):
    if message.name not in connected_users:
        print(f"{message.name} does not exist in the registered users")
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

def handle_subjects_update(message):
    if message.name not in connected_users:
        print(f"{message.name} does not exist in the registered users")
        return Message(
            message_type="SUBJECTS-REJECTED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is not a registered user"
        )
    connected_users[message.name].subjects = message.subjects
    print(f"Updating subjects of user {message.name} to {message.subjects}")
    return Message(
            message_type="SUBJECTS-UPDATED", 
            uuid=message.uuid, 
            name=message.name, 
            subjects=message.subjects
        )

def handle_publish_message(message):
    if message.name not in connected_users:
        print(f"{message.name} does not exist in the registered users")
        return Message(
            message_type="PUBLISH-DENIED", 
            uuid=message.uuid,
            reason=f"`{message.name}` is not a registered user"
        )
    if message.subject not in connected_users[message.name].subjects:
        print(f"User {message.name} is not registered to subject {message.subject}")
        return Message(
            message_type="PUBLISH-DENIED", 
            uuid=message.uuid,
            reason=f"User `{message.name}` is not registered to subject {message.subject}"
        )
    print(f"Publishing message with subject {message.subject}")
    return Message(
        message_type="PUBLISH-CONFIRMED",
        uuid=message.uuid,
    )