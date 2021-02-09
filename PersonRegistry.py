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
from influxdb import InfluxDBClient

ifuser = "<YOUR_INFLUX_DB_USER>"
ifpass = "<YOUR_INFLUX_DB_PASS>"
ifdb = "<YOUR_INFLUX_DB_NAME>"
ifhost = "127.0.0.1"
ifport = 8086


measurement_name = "PersonasRegistradas"

# BD fields:	   ID	    Name		UID		 Course
PersonasUGR =   [
                ["ID_1", "Person_1",  "UID_1", "Course_1"], 
                ["ID_2", "Person_2",  "UID_2", "Course_2"],
                ["ID_3", "Person_3",  "UID_3", "Course_3"],
                ["ID_4", "Person_4",  "UID_4", "Course_4"],
                ["ID_5", "Person_5",  "UID_5", "Course_5"], 
                ]

for i in range(len(PersonasUGR)):
		# Take a timestamp for this measurement
		time = datetime.datetime.utcnow()

		# Format the data as a single measurement for InfluxDB
		body = [
    			{
        			"measurement": measurement_name,
        			"time": time,
        			"fields": {
            				"DNI": PersonasUGR[i][0],
            				"Nombre": PersonasUGR[i][1],
					"UID": PersonasUGR[i][2],
                                        "Curso": PersonasUGR[i][3]
        			}
    			}
		]

		# Connect to InfluxDB
		ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)

		# Write the measurement
		ifclient.write_points(body)
