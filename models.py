ACTION_LIST = ['REGISTER', 'REGISTERED', 'REGISTER-DENIED', 'LOGIN', 'DE-REGISTER', 'UPDATE',
                'UPDATE-CONFIRMED', 'UPDATE-DENIED', 'SUBJECTS', 'SUBJECTS-UPDATED',
                'SUBJECTS-REJECTED', 'PUBLISH', 'PUBLISH-DENIED', "PUBLISH-CONFIRMED" 'MESSAGE', 'CHANGE-SERVER'
                'UPDATE-SERVER']

# Dictionary of names to user objects
connected_users = {}

class Message:
    def __init__(self, message_type=None, uuid=None, name=None, password=None, ip=None, port=None, reason=None, subjects=None, subject=None, text=None):
        self.message_type = message_type
        self.uuid = uuid
        self.name = name
        self.password = password
        self.ip = ip
        self.port = port
        self.reason = reason
        self.subjects = subjects
        self.subject = subject
        self.text = text

    def json_serialize(self):
        return {
            'MESSAGE_TYPE' : self.message_type,
            'RQ' : self.uuid,
            'NAME' : self.name,
            'PASSWORD' : self.password,
            'IP' : self.ip,
            'PORT' : self.port,
            'REASON' : self.reason,
            'SUBJECTS' : self.subjects,
            'SUBJECT' : self.subject,
            'TEXT' : self.text}

    def json_deserialize(self, obj):
        self.message_type = obj['MESSAGE_TYPE']
        self.uuid = obj['RQ']
        self.name = obj['NAME']
        self.password = obj['PASSWORD']
        self.ip = obj['IP']
        self.port = obj['PORT']
        self.reason = obj['REASON']
        self.subjects = obj['SUBJECTS']
        self.subject = obj['SUBJECT']
        self.text = obj['TEXT']

class User:
    def __init__(self, name=None, ip=None, port=None, subjects=set()):
        self.name = name 
        self.ip = ip
        self.port = port 
        self.subjects = subjects