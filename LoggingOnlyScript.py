import webiopi
import datetime
import pymysql.cursors
import RPi.GPIO as GPIO
import time
import threading
import os
import sys
import dateutil.parser
import math
from max6675 import *
#import locale
from webiopi.clients import *
from _ctypes import addressof
from gps import *


cs_pin = 22
clock_pin = 27
data_pin = 17
units = "c"
thermocouple = MAX6675(cs_pin, clock_pin, data_pin, units)
EngineTemp = 0; 
AmbientTemp = 0

gpsd = None #seting the global variable
gpsp = None #
tmp = None

def setup():
    global gpsp
    global tmp
    gpsp = GpsPoller()
    gpsp.start() # start it up
    tmp = webiopi.deviceInstance("temp0")

# loop function is repeatedly called by WebIOPi 
def loop():
  
    webiopi.sleep(20)
  

def destroy():
    global gpsp
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing    
    

def logTemplineDB(location, temp):    
    try:
        connection = pymysql.connect(host='localhost', user='monitor', passwd='password', db='temps', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            cursor.execute ("INSERT INTO tempdat values(NOW(), %s, %s)", (location, temp))
        connection.commit()
        connection.close()
    except:
        print("Temperature Logging Error")

def LogGPSPoint():
    global gpsd
    global EngineTemp
    global AmbientTemp
    global tmp
    
    try:
        con = pymysql.connect(host='localhost', user='monitor', passwd='password', db='temps', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        cur = con.cursor()
    except:
        print ("Error opening MySQL connection")
        sys.exit(1)

    resp = ""
       
    try:
        AmbientTemp = tmp.getCelsius()
    except:
        print("Ambient Temp Read Error")
    
    
    try:
        EngineTemp = thermocouple.get()        
    except MAX6675Error as e:
        EngineTemp = "Error: "+ e.value
#    print("tc: {}".format(tc))
    
    try:    
        if(gpsd.fix.mode == 3 or gpsd.fix.mode == 3):           
        
#             print (' GPS reading')
#             print ('----------------------------------------')
#             print ('latitude    ' , gpsd.fix.latitude)
#             print ('longitude   ' , gpsd.fix.longitude)
            print ('time utc    ' , gpsd.utc)
            print ('time utc    ' , gpsd.fix.time)
#             print ('altitude (m)' , gpsd.fix.altitude)
#             print ('eps         ' , gpsd.fix.eps)
#             print ('epx         ' , gpsd.fix.epx)
#             print ('epv         ' , gpsd.fix.epv)
#             print ('ept         ' , gpsd.fix.ept)
#             print ('speed (m/s) ' , gpsd.fix.speed)
#             print ('climb       ' , gpsd.fix.climb)
#             print ('track       ' , gpsd.fix.track)
#             print ('mode        ' , gpsd.fix.mode)
#     
#             print ('sats        ' , gpsd.satellites)
            
#             if(math.isnan(gpsd.utc) == false):              
#                 fixtime = dateutil.parser.parse(gpsd.utc)
#             else:
#                 fixtime = 0
            
            #print (fixtime)
            sql = "insert into gps(n_lat, w_long, date_time, speed, altitude, mode, track, climb, enginetemp, ambienttemp) values(%s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)" % (gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.speed, gpsd.fix.altitude, gpsd.fix.mode, gpsd.fix.track, gpsd.fix.climb, EngineTemp, AmbientTemp)
            sql = sql.replace("nan", "-9999")
            print (sql)
            cur.execute(sql)
            print ("Rows inserted: %s" % cur.rowcount)
            con.commit()
        else:
            print ("no fix")      

    except:
        print (sys.exc_info()[0])
        print ("excepted")

    finally:
        if con:
            con.close()






class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd #bring it in scope
        gpsd = GPS(mode=WATCH_ENABLE) #starting the stream of info
        self.current_value = None
        self.running = True #setting the thread running to true
 
    def run(self):
        global gpsd
        global gpsp
        while gpsp.running:
            if(gpsd.waiting(3000)):
                gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
                LogGPSPoint()
                webiopi.sleep(3)
 

     
