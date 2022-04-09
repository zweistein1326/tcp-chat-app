#!/usr/bin/python3

# Student name and No.: Siddharth Agarwal
# Development platform: Visual Studio Code MacOS
# Python version: Python3
# Version: Python 3.8.9

import socket
import sys
import select
import json
import time

def main(argv):
    # set port number
    # default is 32342 if no input argument
	if len(argv) == 2:
		port = int(argv[1])
	else:
		port = 40362 #! replace with your port number

	# create socket and bind
	sockfd = socket.socket()
	try:
		sockfd.bind(('', port))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)

	# set socket listening queue
	sockfd.listen(50)

	# add the listening socket to the READ socket list
	RList = [sockfd]

	# create an empty WRITE socket list
	CList = []
	users = []

	# start the main loop
	while True:
		# use select to wait for any incoming connection requests or
		# incoming messages or 10 seconds
		try: 
			Rready, Wready, Eready = select.select(RList, [], [], 10)
		except select.error as emsg:
			print("At select, caught an exception:", emsg)
			sys.exit(1)
		except KeyboardInterrupt:
			sockfd.close()
			print("At select, caught the KeyboardInterrupt")
			sys.exit(1)

		# if has incoming activities
		if Rready:
			# for each socket in the READ ready list
			for sd in Rready:
				# if the listening socket is ready
				# that means a new connection request
				# accept that new connection request
				# add the new client connection to READ socket list
				# add the new client connection to WRITE socket list
				if sd == sockfd:
					newfd, caddr = sockfd.accept()
					if newfd not in RList:
						print("A new client has arrived. It is at:", caddr)
						RList.append(newfd)
						CList.append(newfd)

				# else is a client socket being ready
				# that means a message is waiting or 
				# a connection is broken
				# if a new message arrived, send to everybody
				# except the sender
				# if broken connection, remove that socket from READ 
				# and WRITE lists
				else:
					try:
						rmsg = sd.recv(1000).decode('ascii')
						receivers = []
						if rmsg:
							if rmsg == '1':     					# check if server is connected
								break
							try:
								msg = json.loads(rmsg)
							except :
								print(sys.exc_info())
							# Unknown command
							if(msg["CMD"]=="JOIN" or msg["CMD"]=="SEND"):
								# JOIN
								if(msg["CMD"]=="JOIN"):
									if sd in CList:													# Check if new peer?
										users.append({"UN":msg["UN"],"UID":msg["UID"],"SOCKET":sd}) # Add to peer list
										
										sendAck = '{"CMD":"ACK", "TYPE":"OKAY"}'
										sendList = []												# users without socket address
										
										for user in users:
											sendList.append({"UN":user["UN"],"UID":user["UID"]})
										
										sd.send(sendAck.encode('ascii'))							# SEND ACK - OKAY
										time.sleep(0.2)
										for p in CList:
											p.send(json.dumps({"CMD":"LIST","DATA":sendList}).encode('ascii')) # Send updated peer list to all
								
								if(msg["CMD"]=="SEND"):
									
									fwdMessage = {"CMD":"MSG","TYPE":"PRIVATE","MSG":msg["MSG"],"FROM":msg["FROM"]}
									# Broadcast message
									if(len(msg["TO"])==0):	
										fwdMessage["TYPE"]="ALL"
									# Group message
									elif(len(msg["TO"])>1):
										fwdMessage["TYPE"]="GROUP"
									# Private Message
									else:
										fwdMessage["TYPE"]="PRIVATE"
									# Relay message to all others
									if len(CList) > 1:
										if(len(msg["TO"])>0):
											for receiver in msg["TO"]:
												for user in users:
													if receiver == user["UN"]:
														p = user["SOCKET"]
														if p != sd:
															p.send(json.dumps(fwdMessage).encode('ascii'))
										else:
											for p in CList:
												if p != sd:
													p.send(json.dumps(fwdMessage).encode('ascii'))											
							else:
								# ignore and print a message
								print('Unknown command')
						else:
							RList.remove(sd)	# remove peer from Rlist
							CList.remove(sd)	# remove peer from Clist
							
							tempUsers = []		# Updated Users
							for p in CList:
								for user in users:
									if p == user["SOCKET"]:
										if p != sd:
											tempUsers.append(user)
							
							users = tempUsers
							sendList = []

							# remove client from users
							for user in users:
								sendList.append({"UN":user["UN"],"UID":user["UID"]})
							
							# Send new users list to all users
							sendAck = {"CMD":"LIST","DATA":sendList}
							for p in CList:
								if p != sd:
									p.send(json.dumps(sendAck).encode('ascii'))
					# Handle Broken Connection
					except socket.error as msg:
						if sd in CList:
							RList.remove(sd)	# remove peer from Rlist
							CList.remove(sd)	# remove peer from Clist
							
							tempUsers = []		# Updated Users
							for p in CList:
								for user in users:
									if p == user["SOCKET"]:
										if p != sd:
											tempUsers.append(user)
							
							users = tempUsers
							sendList = []

							# remove client from users
							for user in users:
								sendList.append({"UN":user["UN"],"UID":user["UID"]})
							
							# Send new users list to all users
							sendAck = {"CMD":"LIST","DATA":sendList}
							for p in CList:
								if p != sd:
									p.send(json.dumps(sendAck).encode('ascii'))
						else:
							sendAck = '{"CMD":"ACK", "TYPE":"FAIL"}'
							try:
								sd.send(sendAck.encode('ascii'))
							except:
								print('Connection released')
		# else did not have activity for 10 seconds, 
		# just print out "Idling"
		else:
			print("Idling")


if __name__ == '__main__':
	if len(sys.argv) > 2:
		print("Usage: chatserver [<Server_port>]")
		sys.exit(1)
	main(sys.argv)