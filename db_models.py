from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///rssfeed.db', echo=True)
Base = declarative_base()

user_subject = Table(
    "user_subject",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.user_id")),
    Column("subject_id", Integer, ForeignKey("subject.subject_id")),
)

class Server(Base):
    __tablename__ = "server"

    server_id = Column(Integer, primary_key=True)
    name = Column(String)
    ip = Column(String)
    port = Column(Integer)
    active = Column(Integer)  

    def __init__(self, name, ip, port, active=0):
        self.name = name
        self.ip = ip
        self.port = port  
        self.active = active

    def __repr__(self):
        return f'Server {self.name}'

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    ip = Column(String)
    port = Column(Integer)
    password = Column(String)
    subjects = relationship(
        "Subject", secondary=user_subject, back_populates="users"
    )

    def __init__(self, name, ip, port, password):
        self.name = name
        self.ip = ip
        self.port = port
        self.password = password
    
    def __repr__(self):
        return f'User {self.name}'

class Subject(Base):
    __tablename__ = "subject"

    subject_id = Column(Integer, primary_key=True)
    name = Column(String)
    users = relationship(
        "User", secondary=user_subject, back_populates="subjects"
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'Subject: {self.name}' 


Base.metadata.create_all(engine)