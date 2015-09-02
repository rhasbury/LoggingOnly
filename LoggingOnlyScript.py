#import webiopi
import os
os.system("export QUICK2WIRE_API_HOME=~/temperature/quick2wire-python-api")
os.system("export PYTHONPATH=$PYTHONPATH:$QUICK2WIRE_API_HOME")
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='/home/pi/temperature/Loggingonly.log', level=logging.DEBUG)
import datetime
import pymysql.cursors
import RPi.GPIO as GPIO
import time
import threading
import sys
import dateutil.parser
import math
import signal
import Adafruit_BMP.BMP085 as BMP085

from i2clibraries import i2c_lcd
from max6675 import *
#import locale
from webiopi.clients import *
from _ctypes import addressof
from gps import *

#signal.signal(signal.SIGINT, signal_handler)

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
lcd = None


#def setup():

 # start it up
    #tmp = webiopi.deviceInstance("temp0")

# loop function is repeatedly called by WebIOPi 
#def loop():
  
#    webiopi.sleep(20)
  

#def destroy():
#    global gpsp
#    gpsp.running = False
#    gpsp.join() # wait for the thread to finish what it's doing    
    

def signal_quitting(signal, frame):
    global gpsp
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing        
    logging.info("Received Sigint, quitting")
    logging.info('You pressed Ctrl+C!')    
    sys.exit(0)    


def logTemplineDB(location, temp):    
    try:
        connection = pymysql.connect(host='localhost', user='monitor', passwd='password', db='temps', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            cursor.execute ("INSERT INTO tempdat values(NOW(), %s, %s)", (location, temp))
        connection.commit()
        logging.debug("logTempLineDB() Rows logged: %s" % cursor.rowcount)
        connection.close()
    except:
        logging.error("logTempLineDB Temperature Logging exception Error ", exc_info=True)



def UpdateTemps():
    global EngineTemp
    global AmbientTemp
    global lcd
    global tmp
    if(tmp != None):
        try:
            AmbientTemp = tmp.read_temperature()
            logTemplineDB("ambient", AmbientTemp)
        except:
            print("Ambient Temp Read Error")
    
    
    try:
        EngineTemp = thermocouple.get()
        logTemplineDB("engine", EngineTemp)     
    except KeyboardInterrupt:                        
        raise   
    except MAX6675Error as e:
        #EngineTemp = "Error: "+ e.value
        EngineTemp = -10
        logging.error("UpdateTemps() Excepted getting enginetemp: ", exc_info=True)
    
    if (lcd != None):
        lcdstring = " ET: %3.1sC AT: %3.1sC" % (EngineTemp, AmbientTemp)
        lcd.clear
        lcd.setPosition(1, 0) 
        lcd.writeString(lcdstring)


def LogGPSPoint():
    global gpsd
    global EngineTemp
    global AmbientTemp
    global tmp
    global lcd
 
    resp = ""
   
    try:
        con = pymysql.connect(host='localhost', user='monitor', passwd='password', db='temps', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        cur = con.cursor()
    except KeyboardInterrupt:                        
        raise
    except:
        logging.error("LogGPSPoint: Error opening MySQL connection ", exc_info=True)
        sys.exit(1)

    try:    
        if(gpsd.fix.mode == 3):        
            #print ('time utc    ' , gpsd.utc)
            #print ('time utc    ' , gpsd.fix.time)

            sql = "insert into gps(n_lat, w_long, date_time, speed, altitude, mode, track, climb, enginetemp, ambienttemp) values(%s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)" % (gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.speed, gpsd.fix.altitude, gpsd.fix.mode, gpsd.fix.track, gpsd.fix.climb, EngineTemp, AmbientTemp)
            sql = sql.replace("nan", "-9999")
            cur.execute(sql)
            con.commit()
            logging.debug("Rows inserted: %s" % cur.rowcount)
            logging.debug("SQL String: %s" % sql)
    except KeyboardInterrupt:                        
        raise
    except:
        #print (sys.exc_info()[0])
        logging.error("LogGPSPoint() excepted trying to log GPS data ", exc_info=True)

    finally:
        if con:
            con.close()

    try:
        if(lcd != None and gpsd.fix.mode == 3):            
            lcdstring = "%sm   %s" % (gpsd.fix.altitude, gpsd.fix.track)
            lcd.setPosition(2, 0) 
            lcd.writeString(lcdstring)
            gtime = dateutil.parser.parse(gpsd.utc)            
            lcdstring = "%s" % (gtime.strftime('%I:%M'))
            lcd.setPosition(1, 12)
            lcd.writeString(lcdstring)
        elif(lcd != None and gpsd.fix.mode != 3):
            lcdstring = "No GPS Fix" 
            lcd.setPosition(2, 0) 
            lcd.writeString(lcdstring)                 
            lcdstring = "        " 
            lcd.setPosition(1, 8)
            lcd.writeString(lcdstring)
                    
    except KeyboardInterrupt:                        
        raise
    except:
        logging.error("LogGPSPoint() failed to write to LCD ", exc_info=True) 




class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.current_value = None
        self.running = True #setting the thread running to true

 
    def run(self):
        global gpsd
        global gpsp
        global EngineTemp
        global AmbientTemp
        
        gps_connected = False
        
        while gpsp.running:
            
            try:
                gpsd = GPS(mode=WATCH_ENABLE) #starting the stream of info
                gps_connected = True
            except KeyboardInterrupt:                        
                raise
            except:
                logging.error("GPSPoller() excepted connecting to GPSD ", exc_info=True)
                gps_connected = False

            
            
            while(gps_connected == True):
                if(gpsd.waiting(3000)):                
                    try:
                        gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
                        LogGPSPoint()
                    except JsonError:
                        logging.error("run() -> gpsd.next() threw JsonError", exc_info=True)
                        gps_connected = False                
                    except ValueError:
                        logging.error("run() -> gpsd.next() threw ValueError", exc_info=True)
                        gps_connected = False
                    except StopIteration:                    
                        logging.error("run() -> gpsd.next() threw stopiteration", exc_info=True)
                        gps_connected = False
                    except KeyboardInterrupt:                        
                        raise
                UpdateTemps() 
                time.sleep(0.5)
                
            time.sleep(5)
             
 
 
if __name__ == "__main__":
#    global gpsp
#    global tmp
    try:
        tmp = BMP085.BMP085()
    except:
        logging.error("BMP085 IO Error", exc_info=True)
        tmp = None
        
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Logging started")
    signal.signal(signal.SIGINT, signal_quitting)
    
    # Configuration parameters
    # I2C Address, Port, Enable pin, RW pin, RS pin, Data 4 pin, Data 5 pin, Data 6 pin, Data 7 pin, Backlight pin (optional)
    try:
        lcd = i2c_lcd.i2c_lcd(0x27, 1, 2, 1, 0, 4, 5, 6, 7, 3)
        lcd.backLightOn()
    except IOError:
        logging.error("LCD IO Error", exc_info=True)
        lcd = None
        
    gpsp = GpsPoller()
    gpsp.start()

     
