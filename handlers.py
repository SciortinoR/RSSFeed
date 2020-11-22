from models import *
import db_models

class Handler:
    def __init__(self, server_ID, logger, db_session):
        self.server_ID = server_ID
        self.server_logger = logger
        self.session = db_session

    def handle_register_user(self, message):
        username = message.name
        password = message.password
        ip = message.ip
        port = message.port
        user = self.session.query(db_models.User).filter_by(name=username).one_or_none()

        if user:
            self.server_logger.log_error(self.server_ID, f"`{username}` is already in use")
            return Message(
                message_type="REGISTER-DENIED", 
                uuid=message.uuid,
                reason=f"`{username}` is already in use"
            )
        
        self.server_logger.log_info(self.server_ID, f"Registering new client with name {username} at {ip}:{port}")

        user = db_models.User(username, ip, port, password)
        self.session.add(user)
        self.session.commit()

        return Message("REGISTERED", message.uuid)
    
    def handle_deregister_user(self, message):
        username = message.name
        user = self.session.query(db_models.User).filter_by(name=username).one_or_none()

        if user:
            self.server_logger.log_info(self.server_ID, f"Successfully de-registered user with name {username}")
            self.session.delete(user)
            self.session.commit()
        else:
            self.server_logger.log_warning(self.server_ID, f"`{username}` doesn't exist. Can't de-register.")

    def handle_user_update(self, message):
        username = message.name
        ip = message.ip
        port = message.port
        user = self.session.query(db_models.User).filter_by(name=username).one_or_none()

        if not user:
            self.server_logger.log_error(self.server_ID, f"{username} does not exist in the registered users")
            return Message(
                message_type="UPDATE-DENIED", 
                uuid=message.uuid,
                reason=f"`{username}` is not a registered user"
            )
        self.server_logger.log_info(self.server_ID, f"Updating info for client {username}")

        user.ip = ip
        user.port = port
        self.session.commit()

        return  Message(
                message_type="UPDATE-CONFIRMED", 
                uuid=message.uuid, 
                name=username, 
                ip=message.ip, 
                port=message.port
            )

    def handle_subjects_update(self, message):
        username = message.name
        subjects = message.subjects
        user = self.session.query(db_models.User).filter_by(name=username).one_or_none()

        if not user:
            self.server_logger.log_error(self.server_ID, f"{message.name} does not exist in the registered users")
            return Message(
                message_type="SUBJECTS-REJECTED", 
                uuid=message.uuid,
                reason=f"`{username}` is not a registered user"
            )

        for subject in subjects:
            subject = subject.lower()
            subject_in_db = self.session.query(db_models.Subject).filter_by(name=subject).one_or_none()
            if subject_in_db:
                user.subjects.append(subject_in_db)
            else:
                user.subjects.append(db_models.Subject(subject))
        
        self.session.commit()
        
        self.server_logger.log_info(self.server_ID, f"Updating subjects of user {username} to {subjects}")
        return Message(
                message_type="SUBJECTS-UPDATED", 
                uuid=message.uuid, 
                name=username, 
                subjects=subjects
            )

    def handle_publish_message(self, message):
        username = message.name
        subject = message.subject
        user = self.session.query(db_models.User).filter_by(name=username).one_or_none()
        subject_in_db = self.session.query(db_models.Subject).filter_by(name=subject).one_or_none()

        if not user:
            self.server_logger.log_error(self.server_ID, f"{username} does not exist in the registered users")
            return Message(
                message_type="PUBLISH-DENIED", 
                uuid=message.uuid,
                reason=f"`{username}` is not a registered user"
            )
        if not subject_in_db:
            self.server_logger.log_error(self.server_ID, f"User {username} is not registered to subject {subject}")
            return Message(
                message_type="PUBLISH-DENIED", 
                uuid=message.uuid,
                reason=f"User `{username}` is not registered to subject {subject}"
            )

        self.server_logger.log_info(self.server_ID, f"Publishing message with subject {subject}")
        return Message(
            message_type="PUBLISH-CONFIRMED",
            uuid=message.uuid,
        )