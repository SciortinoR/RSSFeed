import sys
import uuid
import socket
import threading
import win_ctrl_c

from models import Message, ACTION_LIST
from appJar import gui
from json import dumps, loads

win_ctrl_c.install_handler()

WINDOW = ""
USERNAME = ""
LOGGED_IN = False

# Initialize both server IP:PORT with command line args
CURR_SERVER = ()
SERVER1 = sys.argv[1].split(":")
SERVER2 = sys.argv[2].split(":")
SERVER1 = (SERVER1[0], int(SERVER1[1]))
SERVER2 = (SERVER2[0], int(SERVER2[1]))
MAX_BUFFER_SIZE = 1024

# Stop GUI method
def check_stop():
    print("App shutting down...")

    if LOGGED_IN:
        logout(True)

    app.stop()

# Establish initial connection by pinging both servers
def connect(message):
    try:
        udp_client_socket.sendto(dumps(message.json_serialize()).encode(), SERVER1)
        udp_client_socket.sendto(dumps(message.json_serialize()).encode(), SERVER2)
    except socket.error as msg:
        print(msg)
        app.errorBox('Error', msg)

# Send Request
def send(message):
    try:
        udp_client_socket.sendto(dumps(message.json_serialize()).encode(), CURR_SERVER)
    except socket.error as msg:
        print(msg)
        app.errorBox('Error', msg)
    else:
        if message.message_type == "PUBLISH":
            printRSS(message.name, message.subject, message.text)
            

# Submit Unregister
def submit_unregister():
    global USERNAME
    password = app.getEntry('Password')

    send(Message('DE-REGISTER', uuid.uuid4().hex, USERNAME, password))

# Submit Publish
def submit_publish():
    global USERNAME

    subject = app.getEntry("Subject")
    text = app.getTextArea("Text Body")

    send(Message('PUBLISH', uuid.uuid4().hex, USERNAME, subject=subject, text=text))

# Submit Subjects
def submit_subjects():
    global USERNAME

    subjects = [x.strip() for x in app.getEntry("New Subjects List").split(',')]
    
    send(Message('SUBJECTS', uuid.uuid4().hex, USERNAME, subjects=subjects))

# Executes the 'Cancel' button
def destroyWindow():
    global WINDOW

    app.destroySubWindow(WINDOW)
    WINDOW = "Dashboard"

# Update Subjects Window
def update_subjects():
    global WINDOW

    WINDOW = 'Update Subjects'

    app.startSubWindow(WINDOW, modal=True)

    app.setBg("orange")
    app.setFont(18)
    app.addEntry('New Subjects List')
    app.setEntryDefault("New Subjects List", "New Subjects List")
    app.addButtons(["Submit", "Cancel"], [submit_subjects, destroyWindow])

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Publish Window
def publish():
    global WINDOW

    WINDOW = 'Publish'

    app.startSubWindow(WINDOW, modal=True)

    app.setBg("orange")
    app.setFont(18)
    app.addEntry('Subject')
    app.setEntryDefault("Subject", "Subject")
    app.addScrolledTextArea('Text Body')
    app.setTextAreaWidth('Text Body', 35)
    app.setTextAreaHeight('Text Body', 10)
    app.addButtons(["Submit", "Cancel"], [submit_publish, destroyWindow])

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Unregister Window
def unregister():
    global WINDOW

    WINDOW = 'Unregister'

    app.startSubWindow(WINDOW, modal=True)

    app.setBg("orange")
    app.setFont(18)
    app.addSecretEntry("Password")
    app.setEntryDefault("Password", "Password")
    app.addButtons(["Finalize Unregister", "Cancel"], [submit_unregister, destroyWindow])

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Kills UDP Listener thread & logs out to authentication window
def logout(terminate=False):
    global LOGGED_IN
    global udp_listener_running

    LOGGED_IN = False
    udp_listener_running = False
    app.destroyAllSubWindows()
    
    # If close/stop GUI, program terminates without authentication window
    if not terminate or type(terminate) == str:
        authenticate()
    
# User Dashboard Window
def user_window():
    global WINDOW

    app.destroySubWindow(WINDOW)
    WINDOW = "Dashboard"

    app.startSubWindow(WINDOW)

    app.setBg("orange")
    app.setFont(18)
    app.addLabel('dashboard', text=f'Hi {USERNAME}! What would you like to do today:')
    app.addButtons(['Update Subjects', 'Publish'], [update_subjects, publish])
    app.addButtons(['Logout', 'Unregister'], [logout, unregister])
    app.addScrolledTextArea('Feed', text='This is your personal RSS Feed!\n\n')
    app.setTextAreaWidth('Feed', 100)
    app.setTextAreaHeight('Feed', 20)
    app.setTextAreaFont('Feed', size=10)
    app.disableTextArea('Feed')

    app.stopSubWindow()
    app.showSubWindow(WINDOW)

# Displays a message received in the RSS Feed Window
def printRSS(name, subject, text):
    app.setTextArea("Feed", f'[NAME]: {name}\n', end=True, callFunction=False)
    app.setTextArea("Feed", f'[SUBJECT]: {subject}\n', end=True, callFunction=False)
    app.setTextArea("Feed", f'[TEXT]: {text}\n\n', end=True, callFunction=False)

# UDP Listener thread listening for incoming messages from server
def udp_listener():
    global CURR_SERVER

    response = Message()
    while udp_listener_running:
        try:
            response.json_deserialize(loads(udp_client_socket.recvfrom(MAX_BUFFER_SIZE)[0]))

            if response.message_type not in ACTION_LIST:
                raise Exception(f"Undefined Request Type - {response.message_type}")
            elif response.message_type == 'MESSAGE':
                printRSS(response.name, response.subject, response.text)
            elif response.message_type == "SUBJECTS-UPDATED":
                app.infoBox('Update Subjects', "Update Subjects Successful!")
                app.destroySubWindow('Update Subjects')
            elif response.message_type == "PUBLISH-CONFIRMED":
                app.infoBox('Publish', "Publish Successful!")
                app.destroySubWindow('Publish')
            elif response.message_type == "DE-REGISTERED":
                app.infoBox('Unregistered', "Unregister Successful!")
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
    global CURR_SERVER
    global udp_listener_running

    # Gets the username and password entered
    USERNAME = app.getEntry('Username')
    password = app.getEntry('Password')

    response = Message()
    try:
        action = button.upper()

        # Attempt to connect to one of both servers
        connect(Message(action, uuid.uuid4().hex, USERNAME, password, client_access[0], client_access[1]))
        res = udp_client_socket.recvfrom(MAX_BUFFER_SIZE)
        
        # Set active server IP:PORT
        CURR_SERVER = res[1]
        
        response.json_deserialize(loads(res[0]))

        if response.message_type not in ACTION_LIST:
            raise Exception("Undefined Request Type")

        if (action == 'REGISTER' and response.message_type != 'REGISTERED') or (action == 'UPDATE' and response.message_type != 'UPDATE-CONFIRMED'):
            raise Exception(f"Error: {response.message_type}\n\n{response.reason}")
        
    except Exception as msg:
        print(msg)
        app.errorBox('Error', msg)
    else:
        # Launch user dashboard and UDP Listener thread on successful register/login
        user_window()
        LOGGED_IN = True
        udp_listener_running = True
        udp_listener_thread = threading.Thread(target=udp_listener)
        udp_listener_thread.start()

# Authentication Window
def authenticate():
    global WINDOW

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
        # Establish client socket settings
        udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_client_socket.settimeout(3)
        udp_client_socket.bind(("127.0.0.1", 0))
        client_access = udp_client_socket.getsockname()
    except socket.error as msg:
        print("Failed to create client socket")
        app.errorBox(f'Error', 'Failed to create client socket:\n\n{msg}')
        sys.exit()
    else:
        # USP LIstener initially not running on app start, need register/login first
        udp_listener_running = False
        
        # Start GUI with authentication window
        app = gui(handleArgs=False)
        app.topLevel.protocol('WM_DELETE_WINDOW', check_stop)
        authenticate()
        app.go(startWindow="Authentication")