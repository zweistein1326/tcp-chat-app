#!/usr/bin/python3

# Student name and No.: Siddharth Agarwal
# Development platform: Visual Studio Code MacOS
# Python version: Python3
# Version: Python 3.8.9


from tkinter import *
from tkinter import ttk
from tkinter import font
import sys
import socket
import json
import os
import warnings
import threading
import select
import time 

#
# Global variables
#
warnings.filterwarnings("ignore", category=DeprecationWarning) 
MLEN=1000      #assume all commands are shorter than 1000 bytes
USERID = None
NICKNAME = None
SERVER = None
SERVER_PORT = None

SOCKET = socket.socket()
USERS = None 

#
# Functions to handle user input
#

def createThreads():   
  recv_thread = threading.Thread(target = receiveThread)   # create thread for receiving from server
  recv_thread.start()
  
  gui_thread = threading.Thread(target = win.mainloop())   # create thread for UI updates
  gui_thread.start()
  
  # wait for thread to finish executing and release resource
  recv_thread.join()                                       
  gui_thread.join()


def receiveThread():                            # Worker thread - Receive messages
  global USERS
  
  while(True):  
    try:
      rmsg = SOCKET.recv(1000).decode('ascii')  # Wait for message from server
    except:
      console_print('Connection broken')       
      break
    if(rmsg):
      try:
        msg = json.loads(rmsg)
        message = ''
        # Checks for different MSG["CMD"]
        if msg["CMD"]=="ACK" :          # ACK
          if msg["TYPE"]=="OKAY":       # ACK = OKAY
            console_print("Joining")
        if msg["CMD"] == "LIST":        # LIST
            USERS = msg["DATA"]       # Store user info in USERS
            display_string = ''
            for i in range(len(USERS)):
              user = USERS[i]
              if i == len(USERS) - 1 :
                display_string += user["UN"] + ' ({}'.format(user["UID"]) + ') ' 
              else: 
                display_string += user["UN"] + ' ({}'.format(user["UID"]) + '), ' 
            list_print(display_string)
        if msg["CMD"] == "MSG":         # MSG
          for user in USERS:
            if user["UID"] == msg["FROM"]:
              message = '[' + user["UN"]+ '] ' + msg["MSG"]
          if(msg["TYPE"]=="PRIVATE"):
            chat_print(message, "redmsg")
          elif(msg["TYPE"]=="GROUP"):
            chat_print(message, "greenmsg")
          else:
            chat_print(message, "bluemsg")
      except:
        pass
    else:
      SOCKET.close()
      list_print('')
      USERS = None
      console_print('Connection Terminated')

# def send(message):
#   SOCKET.send(message.encode('ascii'))


def do_Join():
    global SOCKET
    try:
      SOCKET.send('1'.encode('ascii'))
    except:
      try:
        SOCKET = socket.socket()
        SOCKET.connect((SERVER, SERVER_PORT))
        # select.select([SOCKET],[],[],2)

        msg = {"CMD":"JOIN", "UN":NICKNAME, "UID":USERID}       # Create JOIN REQUEST
        SOCKET.send(json.dumps(msg).encode('ascii'))            # Send JOIN REQUEST
        
        createThreads()                                         # Start GUI and Receiver THREADS
      except socket.error as msg:
        time.sleep(2)
        console_print('Socket connection error: {}'.format(msg))
        # sys.exit(1)


def do_Send():
  global USERS
  #The following statements are just for demo purpose
  try:
    SOCKET.send('1'.encode('ascii'))  # Send message to check if Socket is connected
    message = get_sendmsg().strip()   # Get message without whitespace
    toList = get_tolist()             # Get all receivers
    newToList = []                    # this list stores all receivers without duplicates
    receiverList = []                 # this list stores all valid receivers
    
    if(message and toList):
      if(toList == "ALL"):  
        # Send broadcast message          
        sendMessage = {"CMD": "SEND", "MSG": message ,"TO":[], "FROM":USERID}     # Create SEND REQUEST
        SOCKET.send(json.dumps(sendMessage).encode('ascii'))                      # Send SEND REQUEST
        chat_print('[To: ALL] ' + message)
      else:       
        # Retrieve name of each sender          
        toList = toList.split(',')
        newToList = list(dict.fromkeys(toList)) # Remove duplicates
        for i in newToList:                     # Remove invalid receivers
          flag = 0
          for j in USERS:
            if(i.strip()==NICKNAME):            # Check if user if trying to send message to self
              console_print('Cannot send message to self')
              break
            if j["UN"] == i.strip():            # Add to list of successful matches
              receiverList.append(i.strip()) 
              flag = 0
              break
            else:                               # If username does not match entry
              flag = 1
          if flag == 1:                         # username does not match entry
            console_print('Cannot send message to unkown ' + i)
   
    if toList and message:             # check if either To: or SEND fields are empty      
      if(len(receiverList)>0):               # check if receivers list is populated
       
        sendMessage = {"CMD": "SEND", "MSG": message, "TO": receiverList , "FROM": USERID}     # Message to send to server
        
        # Message to be displayed on screen
        messageString = '[To: '
        for i in range(len(receiverList)):
          if (i == len(receiverList) - 1):
            messageString +=  receiverList[i] + '] ' + message
          else:
            messageString +=  receiverList[i] + ', '
        chat_print(messageString)  # Display message

        # Send message to server
        try:
          SOCKET.send(json.dumps(sendMessage).encode('ascii'))
        except socket.error as msg:
          print(msg) 
        console_print('sending message')

    else:
      console_print('Either Send field or To: Fields are empty')
  except socket.error as msg:
    console_print('Connect to the server before sending messages {}'.format(msg))
  


def do_Leave():
  global SOCKET
  
  try:
    SOCKET.close()            # Close socket
    list_print('')            # Clear screen
    USERS = None              # Reset USERS
    console_print('Connection Terminated')
  except socket.error as emsg:
    print(emsg)


#################################################################################
#Do not make changes to the following code. They are for the UI                 #
#################################################################################

#for displaying all log or error messages to the console frame
def console_print(msg):
  console['state'] = 'normal'
  console.insert(1.0, "\n"+msg)
  console['state'] = 'disabled'

#for displaying all chat messages to the chatwin message frame
#message from this user - justify: left, color: black
#message from other user - justify: right, color: red ('redmsg')
#message from group - justify: right, color: green ('greenmsg')
#message from broadcast - justify: right, color: blue ('bluemsg')
def chat_print(msg, opt=""):
  chatWin['state'] = 'normal'
  chatWin.insert(1.0, "\n"+msg, opt)
  chatWin['state'] = 'disabled'

#for displaying the list of users to the ListDisplay frame
def list_print(msg):
  ListDisplay['state'] = 'normal'
  #delete the content before printing
  ListDisplay.delete(1.0, END)
  ListDisplay.insert(1.0, msg)
  ListDisplay['state'] = 'disabled'

#for getting the list of recipents from the 'To' input field
def get_tolist():
  msg = toentry.get()
  toentry.delete(0, END)
  return msg

#for getting the outgoing message from the "Send" input field
def get_sendmsg():
  msg = SendMsg.get(1.0, END)
  SendMsg.delete(1.0, END)
  return msg

#for initializing the App
def init():
  global USERID, NICKNAME, SERVER, SERVER_PORT

  #check if provided input argument
  if (len(sys.argv) > 2):
    print("USAGE: ChatApp [config file]")
    sys.exit(0)
  elif (len(sys.argv) == 2):
    config_file = sys.argv[1]
  else:
    config_file = "config.txt"

  #check if file is present
  if os.path.isfile(config_file):
    #open text file in read mode
    text_file = open(config_file, "r")
    #read whole file to a string
    data = text_file.read()
    #close file
    text_file.close()
    #convert JSON string to Dictionary object
    config = json.loads(data)
    USERID = config["USERID"].strip()
    NICKNAME = config["NICKNAME"].strip()
    SERVER = config["SERVER"].strip()
    SERVER_PORT = config["SERVER_PORT"]
  else:
    print("Config file not exist\n")
    sys.exit(0)


if __name__ == "__main__":
  init()

#
# Set up of Basic UI
#
win = Tk()
win.title("ChatApp")

#Special font settings
boldfont = font.Font(weight="bold")

#Frame for displaying connection parameters
topframe = ttk.Frame(win, borderwidth=1)
topframe.grid(column=0,row=0,sticky="w")
ttk.Label(topframe, text="NICKNAME", padding="5" ).grid(column=0, row=0)
ttk.Label(topframe, text=NICKNAME, foreground="green", padding="5", font=boldfont).grid(column=1,row=0)
ttk.Label(topframe, text="USERID", padding="5" ).grid(column=2, row=0)
ttk.Label(topframe, text=USERID, foreground="green", padding="5", font=boldfont).grid(column=3,row=0)
ttk.Label(topframe, text="SERVER", padding="5" ).grid(column=4, row=0)
ttk.Label(topframe, text=SERVER, foreground="green", padding="5", font=boldfont).grid(column=5,row=0)
ttk.Label(topframe, text="SERVER_PORT", padding="5" ).grid(column=6, row=0)
ttk.Label(topframe, text=SERVER_PORT, foreground="green", padding="5", font=boldfont).grid(column=7,row=0)


#Frame for displaying Chat messages
msgframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
msgframe.grid(column=0,row=1,sticky="ew")
msgframe.grid_columnconfigure(0,weight=1)
topscroll = ttk.Scrollbar(msgframe)
topscroll.grid(column=1,row=0,sticky="ns")
chatWin = Text(msgframe, height='15', padx=10, pady=5, insertofftime=0, state='disabled')
chatWin.grid(column=0,row=0,sticky="ew")
chatWin.config(yscrollcommand=topscroll.set)
chatWin.tag_configure('redmsg', foreground='red', justify='right')
chatWin.tag_configure('greenmsg', foreground='green', justify='right')
chatWin.tag_configure('bluemsg', foreground='blue', justify='right')
topscroll.config(command=chatWin.yview)

#Frame for buttons and input
midframe = ttk.Frame(win, relief=RAISED, borderwidth=0)
midframe.grid(column=0,row=2,sticky="ew")
JButt = Button(midframe, width='8', relief=RAISED, text="JOIN", command=do_Join).grid(column=0,row=0,sticky="w",padx=3)
QButt = Button(midframe, width='8', relief=RAISED, text="LEAVE", command=do_Leave).grid(column=0,row=1,sticky="w",padx=3)
innerframe = ttk.Frame(midframe,relief=RAISED,borderwidth=0)
innerframe.grid(column=1,row=0,rowspan=2,sticky="ew")
midframe.grid_columnconfigure(1,weight=1)
innerscroll = ttk.Scrollbar(innerframe)
innerscroll.grid(column=1,row=0,sticky="ns")
#for displaying the list of users
ListDisplay = Text(innerframe, height="3", padx=5, pady=5, fg='blue',insertofftime=0, state='disabled')
ListDisplay.grid(column=0,row=0,sticky="ew")
innerframe.grid_columnconfigure(0,weight=1)
ListDisplay.config(yscrollcommand=innerscroll.set)
innerscroll.config(command=ListDisplay.yview)
#for user to enter the recipents' Nicknames
ttk.Label(midframe, text="TO: ", padding='1', font=boldfont).grid(column=0,row=2,padx=5,pady=3)
toentry = Entry(midframe, bg='#ffffe0', relief=SOLID)
toentry.grid(column=1,row=2,sticky="ew")
SButt = Button(midframe, width='8', relief=RAISED, text="SEND", command=do_Send).grid(column=0,row=3,sticky="nw",padx=3)
#for user to enter the outgoing message
SendMsg = Text(midframe, height='3', padx=5, pady=5, bg='#ffffe0', relief=SOLID)
SendMsg.grid(column=1,row=3,sticky="ew")

#Frame for displaying console log
consoleframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
consoleframe.grid(column=0,row=4,sticky="ew")
consoleframe.grid_columnconfigure(0,weight=1)
botscroll = ttk.Scrollbar(consoleframe)
botscroll.grid(column=1,row=0,sticky="ns")
console = Text(consoleframe, height='10', padx=10, pady=5, insertofftime=0, state='disabled')
console.grid(column=0,row=0,sticky="ew")
console.config(yscrollcommand=botscroll.set)
botscroll.config(command=console.yview)

win.mainloop()