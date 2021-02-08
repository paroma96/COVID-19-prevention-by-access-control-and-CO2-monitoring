#!/usr/bin/env python

//**************************************************************************************************************
//**************************************************************************************************************
//* Title: System for COVID-19 prevention in closed spaces by access control and CO2 monitoring                *
//*                                                                                                            *
//* Authors: Pablo Rodríguez Martín & Daniel García Portero                                                    *
//*                                                                                                            *
//* Date: February 11th, 2021                                                                                  *
//*                                                                                                            * 
//* Version:. 1.0                                                                                              *   
//*                                                                                                            *
//* Type: Python code for control access server (TCP/IP)                                                       *
//*                                                                                                            * 
//* Availability: https://github.com/paroma96/COVID-19-prevention-by-access-control-and-CO2-monitoring/import  *
//*                                                                                                            *  
//**************************************************************************************************************
//**************************************************************************************************************
 
import datetime
import socket
import sys
import time
from influxdb import InfluxDBClient

ifuser = "<YOUR_INFLUX_DB_USER>"
ifpass = "<YOUR_INFLUX_DB_PASS>"
ifdb = "<YOUR_INFLUX_DB_NAME>"
ifhost = "127.0.0.1"
ifport = 8086
client = InfluxDBClient(ifhost, ifport, ifuser, ifpass, ifdb)
NUM_PERSON_MAX = 20
        
        
#DEFINITION OF FUNCTIONS
# Receiving UID from client
def receiveCode():
    data = ""
    data = conn.recv(70)
    #print(data)
    return(data)


#Get the number of people in the room
def getNumPerson():	
    	results = client.query("SELECT last(Npersonas) from NpersonasClase")
	#print results
        if not results:
            return 0
        else:
    	    points = results.get_points()
    	    for item in points:
                    return item['last']


#Write the number of people in the room to the DB
def writeNumPerson(Numero):
	# Take a timestamp for this measurement
	time = datetime.datetime.utcnow()

	measurement_name = "NpersonasClase"
	# Format the data as a single measurement for influx
	body = [
    		{
        		"measurement": measurement_name,
        		"time": time,
        		"fields": {
            			"Npersonas": Numero
        		}
    		}
	]
	# Write the measurement
	client.write_points(body)


# Check that the received UID appears in the database
# return 1 if UID appears
def checkUID(UID):
        results = client.query(("SELECT * from PersonasRegistradas where UID='%s'") % (UID))
        #print(results)
        if not results:
            check=0
        else:
            check=1
        #print(check)
	return check


# Get State
def getState(UID):
    	results = client.query(("SELECT last(Estado) from PersonalUGR where UID='%s'") % (UID))
        #print results
    	points = results.get_points()
    	for item in points:
        	return item['last']
            

# Get DNI
def getDNI(UID):
    	results = client.query(("SELECT last(DNI) from PersonasRegistradas where UID='%s'") % (UID))
	#print results
    	points = results.get_points()
    	for item in points:
        	return item['last']
            
            
# Get Name
def getName(UID):
    	results = client.query(("SELECT last(Nombre) from PersonasRegistradas where UID='%s'") % (UID))
	#print results
    	points = results.get_points()
    	for item in points:
        	return item['last']


# Get Course
def getCourse(UID):
    	results = client.query(("SELECT last(Curso) from PersonasRegistradas where UID='%s'") % (UID))
	#print results
    	points = results.get_points()
    	for item in points:
        	return item['last']


# Write change in the state of a person in the DB
def writeChange(UID):
	measurement_name = "PersonalUGR"
	DNI = getDNI(UID)
	Nombre = getName(UID)
	Curso = getCourse(UID)
	Estado = getState(UID)
	
	if(Estado == 0 or not Estado):
		Estado = 1
	else:
		Estado = 0

	# Take a timestamp for this measurement
	time = datetime.datetime.utcnow()

	# Format the data as a single measurement for influx
	body = [
   			{
        			"measurement": measurement_name,
        			"time": time,
        			"fields": {
            				"DNI": DNI,
            				"Nombre": Nombre,
					"UID": UID,
					"Curso": Curso,
					"Estado": Estado 
        			}
    			}
		]
	# Write the measurement
	client.write_points(body)


# Gives access only for course "1-MUIT" or "Docente"
def grantAccess(UID):
    access = ''
    verificacionUID = checkUID(UID)

    if (verificacionUID==1):
    	course = getCourse(UID)
        numPerson = getNumPerson()
	state = getState(UID)

    	if((course == "1-MUIT" or course == "Docente") and (state == 0 or not state) and numPerson < NUM_PERSON_MAX): # Person enters
            access = "Granted"
            print("Access Granted to registered UID %s" % (UID))
	    writeNumPerson(numPerson+1)
	    writeChange(UID)
    	elif((course == "1-MUIT" or course == "Docente") and state == 1):  # Person exits
            access = "Granted"
            print("User with UID %s left the class" % (UID))
	    writeNumPerson(numPerson-1)
	    writeChange(UID)
	else:
	    access = "Blocked"
            print("Access Denied to registered UID %s" % (UID))
    else:
	access = "Unknown"
        print("ERROR: UNKNOWN UID")

    return (access);


# Send authorized/denied permission to client
def sendPermission(permission):
    conn.send(permission)
    print("permission sent")


# Students' registration and main connection with client 
def securitySystem():
    UID = ''
    # Wait to accept a connection - blocking call
    print('Connected with', addr)
    UID = receiveCode()
    permission = grantAccess(UID)
    sendPermission(permission)
    

# MAIN **************************************************************
try:
    # Definition of network parameters
    HOST = '192.168.1.132' # RPi's IP static address
    PORT = 8085 # Service port

    # Creation of the network socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print 'Socket created'

    # Binding of the network socket
    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
          
    print 'Socket bind complete'

    # Start listening on socket
    s.listen(1)
    print 'Socket now listening at'
    print(s.getsockname())
    while(1):
        try:
            conn, addr = s.accept()
            conn.settimeout(300) # Waits for 300 seconds/5 minutes until creating new connection to avoid failures
            securitySystem()
            conn.close()
        except socket.timeout as e:
            print(e)
            conn.close()
except KeyboardInterrupt:
    print("")
    print("Shutting off server")
    conn.close()
    s.close()
    sys.exit()
