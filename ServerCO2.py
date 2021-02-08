#!/usr/bin/env python

//**************************************************************************************************************
//**************************************************************************************************************
//* Title: System for COVID-19 prevention in closed spaces by access control and CO2 monitoring                *
//*                                                                                                            *
//* Authors: Pablo Rodríguez Martín & Daniel García Portero                                                    *
//*                                                                                                            *
//* Date: February 11th, 2021                                                                                  *
//*                                                                                                            * 
//* Version: 1.0                                                                                               *   
//*                                                                                                            *
//* Type: Python code for CO2 server (UDP/IP)                                                                  *
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

        
# DEFINITION OF FUNCTIONS
# Get data from SensorCO2 database
def getValSensorCO2():
	results = client.query("SELECT last(Datos) from SensorCO2")
	print results
    	points = results.get_points()
    	for item in points:
		print item['last']
        	return item['last']


# Save data from SensorCO2 to SensorCO2 database
def writeValSensorCO2(valor):
	# Take a timestamp for this measurement
	time = datetime.datetime.utcnow()
	measurement_name = "SensorCO2"
        valor = int(valor)
	# Format the data as a single measurement for influx
	body = [
    		{
        		"measurement": measurement_name,
        		"time": time,
        		"fields": {
            			"Datos": valor
        		}
    		}
	]

	# Write the measurement
	client.write_points(body)
    

# Receiving data from client
def receiveCode():
    data = 0
    data,addr = s.recvfrom(200) # Test: echo "40305" > /dev/udp/192.168.1.132/8084
    return(data,addr)
    

# CO2 registration and main connection with client  **IDEM FUNCION SETUPSTUDENT
def measureSystem():
    co2Value = 0 #ppm
    co2Value,addr=receiveCode()
    print('Message received from', addr)
    print(co2Value)
    writeValSensorCO2(co2Value)
    

# MAIN **************************************************************
try:
    # Definition of network parameters
    HOST = '192.168.1.132' # RPi's IP static address
    PORT = 8084 # Service port

    # Creation of the network socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print 'Socket created'

    # Binding of the network socket
    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
          
    print 'Socket bind complete'

    # Start listening on socket
    print 'Socket now listening at'
    print(s.getsockname())
    while(1):
        measureSystem()
except KeyboardInterrupt:
    print("")
    print("Shutting off server")
    s.close()
    sys.exit()
