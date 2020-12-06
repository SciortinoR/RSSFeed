import sys
import uuid
import socket
import threading
import win_ctrl_c

from models import *
from appJar import gui
from json import dumps, loads

win_ctrl_c.install_handler()

WINDOW = ""
USERNAME = ""
LOGGED_IN = False

CURR_SERVER = ()
SERVER1 = sys.argv[1].split("::")
SERVER2 = sys.argv[2].split("::")
SERVER1 = (SERVER1[0], int(SERVER1[1]))
SERVER2 = (SERVER2[0], int(SERVER2[1]))
MAX_BUFFER_SIZE = 1024

# Stop GUI method
def check_stop():
    print("App shutting down...")

    if LOGGED_IN:
        logout(True)

    app.stop()

# Initial connect to both servers
def connect(message):
    global CURR_SERVER

    try:
        udp_client_socket.sendto(dumps(message.json_serialize()).encode(), SERVER1)
    except socket.error as msg:
        pass
    else:
        CURR_SERVER = SERVER1
        return
    try:
        udp_client_socket.sendto(dumps(message.json_serialize()).encode(), SERVER2)
    except socket.error as msg:
        print(msg)
        app.errorBox('Error', msg)
    else:
        CURR_SERVER = SERVER2

# Send Request 
def send(message):
    try:
        udp_client_socket.sendto(dumps(message.json_serialize()).encode(), CURR_SERVER)
    except socket.error as msg:
        print(msg)
        app.errorBox('Error', msg)

# Submit Unregister
def submit_unregister():
    username = app.getEntry('Username')
    password = app.getEntry('Password')

    send(Message('DE-REGISTER', uuid.uuid4().hex, username, password))

# Submit Publish
def submit_publish():
    username = app.getEntry('Username')
    subject = app.getEntry("Subject")
    text = app.getTextArea("Text Body")

    send(Message('PUBLISH', uuid.uuid4().hex, username, subject=subject, text=text))

# Submit Subjects
def submit_subjects():
    username = app.getEntry('Username')
    subjects = [x.strip() for x in app.getEntry("New Subjects List").split(',')]
    
    send(Message('SUBJECTS', uuid.uuid4().hex, username, subjects=subjects))
    
# Submit Info
def submit_info():
    ip = app.getEntry('New IP Address')
    port = app.getEntry('New Socket #')

    send(Message('UPDATE', uuid.uuid4().hex, USERNAME, ip=ip, port=port))

# Update Subjects Window
def update_subjects():
    global WINDOW

    app.destroySubWindow(WINDOW)
    WINDOW = 'Update Subjects'

    app.startSubWindow(WINDOW)
    app.setBg("orange")
    app.setFont(18)
    app.addEntry('Username')
    app.setEntry("Username", USERNAME)
    app.addEntry('New Subjects List')
    app.setEntryDefault("New Subjects List", "New Subjects List")
    app.addButtons(["Submit", "Cancel"], [submit_subjects, user_window])

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Publish Window
def publish():
    global WINDOW

    app.destroySubWindow(WINDOW)
    WINDOW = 'Publish'

    app.startSubWindow(WINDOW)

    app.setBg("orange")
    app.setFont(18)
    app.addEntry('Username')
    app.setEntry("Username", USERNAME)
    app.addEntry('Subject')
    app.setEntryDefault("Subject", "Subject")
    app.addScrolledTextArea('Text Body')
    app.setTextAreaWidth('Text Body', 35)
    app.setTextAreaHeight('Text Body', 10)
    app.addButtons(["Submit", "Cancel"], [submit_publish, user_window])

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Unregister Window
def unregister():
    global WINDOW

    app.destroySubWindow(WINDOW)
    WINDOW = 'Unregister'

    app.startSubWindow(WINDOW)

    app.setBg("orange")
    app.setFont(18)
    app.addEntry('Username')
    app.setEntry("Username", USERNAME)
    app.addSecretEntry("Password")
    app.setEntryDefault("Password", "Password")
    app.addButtons(["Finalize Unregister", "Cancel"], [submit_unregister, user_window])

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Kill RSS Feed + Logout
def logout(terminate=False):
    global LOGGED_IN
    global udp_listener_running

    LOGGED_IN = False
    udp_listener_running = False
    app.destroySubWindow('RSS Feed')
    
    if not terminate or type(terminate) == str:
        authenticate()
    
# User Dashboard Window
def user_window():
    global WINDOW

    app.setLabelBg("status", "green")

    app.destroySubWindow(WINDOW)
    WINDOW = "Dashboard"

    app.startSubWindow(WINDOW)

    app.setBg("orange")
    app.setFont(18)
    app.addLabel('dashboard', text=f'Hi {USERNAME}! What would you like to do today:')
    app.addButtons(['Update Subjects', 'Publish'], [update_subjects, publish])
    app.addButtons(['Logout', 'Unregister'], [logout, unregister])
    
    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# RSS Feed Window
def rss_window():
    app.startSubWindow('RSS Feed')

    app.addScrolledTextArea('Feed', text='This is your personal RSS Feed!\n\n')
    app.setTextAreaWidth('Feed', 100)
    app.setTextAreaHeight('Feed', 20)
    app.setTextAreaFont('Feed', size=10)
    app.disableTextArea('Feed')

    app.stopSubWindow()
    app.showSubWindow('RSS Feed')

# Listens to incoming messages from server
def udp_listener():
    global CURR_SERVER

    response = Message()
    while udp_listener_running:
        try:
            response.json_deserialize(loads(udp_client_socket.recvfrom(MAX_BUFFER_SIZE)[0]))

            if response.message_type not in ACTION_LIST:
                raise Exception(f"Undefined Request Type - {response.message_type}")
            elif response.message_type == 'MESSAGE':
                app.setTextArea("Feed", f'[NAME]: {response.name}\n', end=True, callFunction=False)
                app.setTextArea("Feed", f'[SUBJECT]: {response.subject}\n', end=True, callFunction=False)
                app.setTextArea("Feed", f'[TEXT]: {response.text}\n\n', end=True, callFunction=False)
            elif response.message_type == "SUBJECTS-UPDATED":
                app.errorBox('Update Subjects', "Update Subjects Successful!")
                user_window()
            elif response.message_type == "PUBLISH-CONFIRMED":
                app.errorBox('Publish', "Publish Successful!")
                user_window()
            elif response.message_type == "DE-REGISTERED":
                app.errorBox('Unregistered', "Unregister Successful!")
                logout()
            elif response.message_type == "CHANGE-SERVER":
                CURR_SERVER = (response.ip, response.port)
                print(f"Changing server to: {CURR_SERVER}")
            else:
                raise Exception(f"Error: {response.message_type}\n\n{response.reason}")
        except socket.timeout:
            continue
        except Exception as msg:
            print(msg)
            app.errorBox('Error', msg)

# Confirm Register/Login
def register_login(button):
    global USERNAME
    global LOGGED_IN
    global udp_listener_running

    USERNAME = app.getEntry('Username')
    password = app.getEntry('Password')

    response = Message()
    try:
        action = button.upper()
        connect(Message(action, uuid.uuid4().hex, USERNAME, password, client_access[0], client_access[1]))
        response.json_deserialize(loads(udp_client_socket.recvfrom(MAX_BUFFER_SIZE)[0]))

        if response.message_type not in ACTION_LIST:
            raise Exception("Undefined Request Type")

        if (action == 'REGISTER' and response.message_type != 'REGISTERED') or (action == 'UPDATE' and response.message_type != 'UPDATE-CONFIRMED'):
            raise Exception(f"Error: {response.message_type}\n\n{response.reason}")

    except Exception as msg:
        print(msg)
        app.errorBox('Error', msg)
    else:
        user_window()
        rss_window()
        LOGGED_IN = True
        udp_listener_running = True
        udp_listener_thread = threading.Thread(target=udp_listener)
        udp_listener_thread.start()

# Authentication Window
def authenticate():
    global WINDOW

    app.setLabelBg("status", "red")

    if WINDOW:
        app.destroySubWindow(WINDOW)
    WINDOW = "Authentication"

    app.startSubWindow(WINDOW)

    app.setBg("orange")
    app.setFont(18)
    app.addEntry("Username")
    app.addSecretEntry("Password")
    app.setEntryDefault("Username", "Username")
    app.setEntryDefault("Password", "Password")
    app.addButtons(["Register", "Update"], register_login)

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

if __name__ == '__main__':
    try:
        udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_client_socket.settimeout(3)
        udp_client_socket.bind(("", 0))
        client_access = udp_client_socket.getsockname()
    except socket.error as msg:
        print("Failed to create client socket")
        app.errorBox(f'Error', 'Failed to create client socket:\n\n{msg}')
        sys.exit()
    else:
        udp_listener_running = False
        
        app = gui("Status", "210x22", handleArgs=False)
        app.setFont(20)
        app.addLabel('status', 'RSS MANAGER')
        app.setLabelBg("status", "red")
        app.setLabelFg("status", "black")
        app.topLevel.protocol('WM_DELETE_WINDOW', check_stop)
        authenticate()
        app.go()