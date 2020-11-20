from models import *

def handle_register_user(message):
    if message.name in connected_users:
        print(f"`{message.name}` is already in use")
        return Message(
            "REGISTER-DENIED", 
            message.uuid,
            f"`{message.name}` is already in use"
            )
    
    print(f"Registering new client with name {message.name} at {message.ip}:{message.port}")
    connected_users[message.name] = User(message.name, message.ip, message.port)
    return Message("REGISTERED", message.uuid)


def handle_user_update(message):
    if message.name not in connected_users:
        print(f"{message.name} does not exist in the registered users")
        return Message(
            "UPDATE-DENIED", 
            message.uuid,
            f"`{message.name}` is not a registered user"
            )
    print(f"Updating info for client {message.name}")
    connected_users[message.name] = User(message.name, message.ip, message.port)
    return  Message("UPDATE-CONFIRMED", 
                    message.uuid, 
                    message.name, 
                    message.ip, 
                    message.port
                )

def handle_subjects_update(message):
    if message.name not in connected_users:
        print(f"{message.name} does not exist in the registered users")
        return Message(
            "SUBJECTS-REJECTED", 
            message.uuid,
            f"`{message.name}` is not a registered user"
            )
    connected_users[message.name].subjects = message.subjects
    print(f"Updating subjects of user {message.name} to {message.subjects}")
    return Message(
            "SUBJECTS-UPDATED", 
            message.uuid, 
            message.name, 
            subjects=message.subjects
        )

def handle_publish_message(message):
    if message.name not in connected_users:
        print(f"{message.name} does not exist in the registered users")
        return Message(
            "PUBLISH-DENIED", 
            message.uuid,
            f"`{message.name}` is not a registered user"
            )
    print(f"Publishing message with subject {message.subject}")
    return Message(
        "PUBLISH-CONFIRMED",
        message.uuid,
    )