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
//* Type: Python code for Positive-COVID monitoring                                                            *
//*                                                                                                            * 
//* Availability: https://github.com/paroma96/COVID-19-prevention-by-access-control-and-CO2-monitoring/import  *
//*                                                                                                            *  
//**************************************************************************************************************
//**************************************************************************************************************

import datetime
import socket
import sys
import time
from datetime import datetime, date, time, timedelta
from influxdb import InfluxDBClient


ifuser = "<YOUR_INFLUX_DB_USER>"
ifpass = "<YOUR_INFLUX_DB_PASS>"
ifdb = "<YOUR_INFLUX_DB_NAME>"
ifhost = "127.0.0.1"
ifport = 8086
client = InfluxDBClient(ifhost, ifport, ifuser, ifpass, ifdb)


#DEFINITION OF FUNCTIONS
# Get State
def getState(UID):
  results = client.query(("SELECT last(Estado) from PersonalUGR where UID='%s'") % (UID))
  points = results.get_points()
  for item in points:
    return item['last']


# Get DNI
def getDNI(UID):
  results = client.query(("SELECT last(DNI) from PersonasRegistradas where UID='%s'") % (UID))
  points = results.get_points()
  for item in points:
    return item['last']
      
      
# Get Name
def getName(UID):
  results = client.query(("SELECT last(Nombre) from PersonasRegistradas where UID='%s'") % (UID))
  points = results.get_points()
  for item in points:
    return item['last']


# Get Course
def getCourse(UID):
  results = client.query(("SELECT last(Curso) from PersonasRegistradas where UID='%s'") % (UID))
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


# Modify internal lower search time in -5min
def adapTimeInf(Time):
  Time_obj = datetime.strptime(Time, '%Y-%m-%dT%H:%M:%S.%fZ')
  TimeInf = Time_obj - timedelta(minutes=5)
  TimeInf = TimeInf.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
  return TimeInf


# Modifica el tiempo superior de busqueda en +-5min  
def adapTimeSup(Time):
  Time_obj = datetime.strptime(Time, '%Y-%m-%dT%H:%M:%S.%fZ')
  TimeSup = Time_obj + timedelta(minutes=5)
  TimeSup = TimeSup.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
  return TimeSup


# Delete repeated UIDs and the positive-COVID person's 
def getUIDsNoRept(UID,UID_covid):
  UID_Final = []
  for i in range (len(UID)):
    if(UID[i]!=UID_covid and not(UID[i] in UID_Final)):
      UID_Final.append(UID[i])
  return UID_Final
  
  
# Show the results of the search
def mostrarResultados(UID_F):
  print "\nPeople i contact with Positive-COVID person:"
  print('{0:<23} {1:>15} {2:>10}'.format('Nombre','DNI','Curso') )
  for i in range (len(UID_F)):
    Name = getName(UID_F[i])
    DNI = getDNI(UID_F[i])
    Course = getCourse(UID_F[i])
    print('{0:<23} {1:>15} {2:>10}'.format(Name,DNI,Course) )
    
    
# MAIN *********************************************************
Estado = []
Time = []
UID = []

# Data insertion
date = raw_input('Start date of search (Format: YYYY-MM-DD HH:MM:SS): ')
UID_covid = raw_input('Insert COVID-infected person´s UID: ')

# Obtain state changes of positive-COVID person with timestamps
results = client.query(("SELECT Estado from PersonalUGR where UID='%s' AND time >= '%s'")%(UID_covid,date))
points = results.get_points()

for item in points:
  Estado.append(item['Estado'])
  Time.append(item['time'])

# Search of people on contact with positive-COVID person by time coincidences at the same place
# Starting by state 1
if(Estado[0]==1 and (len(Estado)%2==0)):
  for i in range (0, len(Estado), 2):
    Time1 = adapTimeInf(Time[i])
    Time2 = adapTimeSup(Time[i+1])
    results = client.query(("SELECT UID from PersonalUGR where Estado=1 AND time >= '%s' AND time <= '%s'")%(Time1,Time2))
    points = results.get_points()  
    for item in points:
      UID.append(item['UID'])
elif(Estado[0]==1 and (len(Estado)%2!=0)):
  for i in range (0, len(Estado), 2):
    if(i!=len(Estado)-1):
      Time1 = adapTimeInf(Time[i])
      Time2 = adapTimeSup(Time[i+1])
      results = client.query(("SELECT UID from PersonalUGR where Estado=1 AND time>='%s' AND time<='%s'")%(Time1,Time2))
    else:
      Time1 = adapTimeInf(Time[i])
      results = client.query(("SELECT UID from PersonalUGR where Estado=1 AND time>='%s'")%(Time1)) 
    points = results.get_points()
    for item in points:
      UID.append(item['UID'])
        
# Starting by state 0     
elif(Estado[0]==0 and (len(Estado)%2!=0)):
  for i in range (1, len(Estado), 2):
    Time1 = adapTimeInf(Time[i])
    Time2 = adapTimeSup(Time[i+1])
    results = client.query(("SELECT UID from PersonalUGR where Estado=1 AND time >= '%s' AND time <= '%s'")%(Time1,Time2))
    points = results.get_points()
    for item in points:
      UID.append(item['UID'])
elif(Estado[0]==0 and (len(Estado)%2==0)):
  for i in range (1, len(Estado), 2):
    if(i!=len(Estado)-1):
      Time1 = adapTimeInf(Time[i])
      Time2 = adapTimeSup(Time[i+1])
      results = client.query(("SELECT UID from PersonalUGR where Estado=1 AND time >= '%s' AND time <= '%s'")%(Time1,Time2))
    else:
      Time1 = adapTimeInf(Time[i])
      results = client.query(("SELECT UID from PersonalUGR where Estado=1 AND time>='%s'")%(Time1)) 
    points = results.get_points()
    for item in points:
      UID.append(item['UID'])  
else:
  print "ERROR"
  
# Delete repeated UIDs and the positive-COVID person's 
UID_F = getUIDsNoRept(UID,UID_covid) 
   
# Show a list of person resulted to be in contact with positive-COVID person
mostrarResultados(UID_F)   
