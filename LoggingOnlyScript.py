#import webiopi
import os
os.system("export QUICK2WIRE_API_HOME=~/temperature/quick2wire-python-api")
os.system("export PYTHONPATH=$PYTHONPATH:$QUICK2WIRE_API_HOME")
os.system("export MPU6050_PATH=~/temperature/MPU6050")
os.system("export PYTHONPATH=$PYTHONPATH:$MPU6050_PATH")
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='/home/pi/temperature/Loggingonly.log', level=logging.DEBUG)
import datetime
import pymysql.cursors
import RPi.GPIO as GPIO
import time
from time import mktime
from datetime import timedelta
import threading
import sys
import dateutil.parser
import math
import signal
import Adafruit_BMP.BMP085 as BMP085
import collections

from i2clibraries import i2c_lcd
from max6675 import *
#import locale
from webiopi.clients import *
from _ctypes import addressof
from gps import *
from MPU6050 import sensor

#signal.signal(signal.SIGINT, signal_handler)

logradius = 0.0001 # lattitude/long must change by this value to be saved to mysql
cs_pin = 22
clock_pin = 27
data_pin = 17
units = "c"
thermocouple = MAX6675(cs_pin, clock_pin, data_pin, units)
EngineTemp = 0; 
AmbientTemp = 0

oldlong = 0 
oldlat = 0 

oldktemp = 0
tempqlen = 10
ktempq = collections.deque(maxlen=tempqlen)




lcdline1 = "   starting     "
lcdline2 = "     now        "
lcdline3 = "     roll       "


gpsd = None #seting the global variable
gpsp = None #
tmp = None
lcd = None


def signal_quitting(signal, frame):
    global gpsp
    logging.info("Received Sigint, killing threads and waiting for join. ")
    
    gpsp.running = False
    tempthread.running = False
    lcdthread.running = False
    
    ninedof.stop()
    
    gpsp.join(2) # wait for the thread to finish what it's doing
    logging.info("gps thread killed, quitting")
    lcdthread.join(2)
    logging.info("lcd update thread killed, quitting")
    tempthread.join(2)
    logging.info("temperature updating thread killed, quitting")
    logging.info("all threads killed, quitting")
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
    global lcdline1
    global lcdline2
    global lcdline3    
    global tmp
    global oldktemp
    
    if(tmp != None):
        try:
            AmbientTemp = tmp.read_temperature()
            logTemplineDB("ambient", AmbientTemp)
        except:
            logging.error("UpdateTemps() Ambient Temp Read Error: ", exc_info=True)

    try:
        EngineTemp = thermocouple.get()
        if(EngineTemp < 200 ):                  # check to remove unrealistic measurements....which happen frequently due to engine/ignition noise.              
            ktempq.append(EngineTemp)            
            qavg = sum(ktempq) / ktempq.__len__()
            if(abs(EngineTemp-qavg) < 10):
                logTemplineDB("engine", EngineTemp)
                lcdline1 = "E:%4.1fC A:%4.1fC" % (EngineTemp, AmbientTemp)  
    except KeyboardInterrupt:                        
        raise   
    except MAX6675Error as e:
        #EngineTemp = "Error: "+ e.value
        EngineTemp = -10
        logging.error("UpdateTemps() Excepted getting enginetemp: ", exc_info=True)
    
    
    
    if(ninedof != None):
        try:
            roll = ninedof.roll
            #lcdline3 = "Roll: %4.1f " % (ninedof.roll)
            roll = roll + 90
            charposition = round(abs(roll/12)) 
            s = "              "
            if (charposition < 15) :
                lcdline3 = s[:charposition] + 'O' + s[charposition:]
    
        except:
            logging.error("UpdateTemps() ninedof sensor couldn't be read", exc_info=True)
        #print (lcdstring)



def LogGPSPoint():
    global gpsd
    global EngineTemp
    global AmbientTemp
    global lcdline1
    global lcdline2   
    global logradius
    resp = ""
   
    global oldlat
    global oldlong
   
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
            gtime = dateutil.parser.parse(gpsd.utc) - timedelta(hours=4)
            logging.debug("difference in old points {0}, {1} ".format(abs(oldlat - gpsd.fix.latitude), abs(oldlong - gpsd.fix.longitude)))
            if(abs(oldlat - gpsd.fix.latitude) > logradius or abs(oldlong - gpsd.fix.longitude) > logradius):                 
                #print ('time utc    ' , gpsd.utc)
                #print ('time utc    ' , gpsd.fix.time)                
                sql = "insert into gps(n_lat, w_long, date_time, fix_time, speed, altitude, mode, track, climb, enginetemp, ambienttemp, satellites) values(%s, %s, NOW(), FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s, %s, %s)" % (gpsd.fix.latitude, gpsd.fix.longitude, mktime(gtime.timetuple()), gpsd.fix.speed, gpsd.fix.altitude, gpsd.fix.mode, gpsd.fix.track, gpsd.fix.climb, EngineTemp, AmbientTemp, len(gpsd.satellites))
                sql = sql.replace("nan", "-9999")
                cur.execute(sql)
                con.commit()                
                oldlat = gpsd.fix.latitude
                oldlong = gpsd.fix.longitude
                logging.debug("Rows inserted: %s" % cur.rowcount)
                logging.debug("SQL String: %s" % sql)
            lcdline2 = "%4.1fm %3.1f %s" % (gpsd.fix.altitude, (gpsd.fix.speed * 3.6), gtime.strftime('%I:%M'))
        elif(gpsd.fix.mode != 3):
            lcdline2 = "No GPS Fix      "
    
    
    
    except KeyboardInterrupt:                        
        raise
    except:
        #print (sys.exc_info()[0])
        logging.error("LogGPSPoint() excepted trying to log GPS data ", exc_info=True)

    finally:
        if con:
            con.close()
      
     




class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.current_value = None
        self.running = True #setting the thread running to true

 
    def run(self):
        global gpsd
        global gpsp
        
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

            
            oldtime = time.time()
            while(gps_connected == True):
                if(gpsd.waiting(3000)):                
                    try:                        
                        gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
                        logging.debug("seconds passed since last GPS sentence: %s", (time.time() - oldtime))
                        if(time.time() - oldtime > 2):                            
                            oldtime = time.time()
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
                
                #time.sleep(0.5)
                
            #time.sleep(5)
             
 
 
 
class LcdUpdate(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.current_value = None
        self.running = True #setting the thread running to true 
        
        
    def run(self):
        global lcd
        global lcdline1
        global lcdline2                 
        while self.running:
            lcd.clear
            lcd.setPosition(1, 0) 
            lcd.writeString(lcdline1)
            lcd.setPosition(2, 0) 
            lcd.writeString(lcdline3)
            logging.debug("LCDString1: %s" % lcdline1)
            logging.debug("LCDString2: %s" % lcdline2)
            time.sleep(0.2)
             

 
 
 
class TempUpdates(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.current_value = None
        self.running = True #setting the thread running to true 
        
        
    def run(self):                 
        while self.running:
            UpdateTemps()
            time.sleep(0.2)
            
 
 
if __name__ == "__main__":


    # Check for connected BMP085 sensor
    try:
        tmp = BMP085.BMP085()
    except:
        logging.error("BMP085 IO Error", exc_info=True)
        tmp = None


    # Check for connected MPU6050 sensor
    try:
        ninedof = sensor.sensor()
        ninedof.start()
    except IOError:
        logging.error("9dof sensor init error", exc_info=True)
        ninedof = None

    # Create logger and set options
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Logging started")
    signal.signal(signal.SIGINT, signal_quitting)
    
    # Check for Connected LCD and configure
    # Configuration parameters
    # I2C Address, Port, Enable pin, RW pin, RS pin, Data 4 pin, Data 5 pin, Data 6 pin, Data 7 pin, Backlight pin (optional)
    try:
        lcd = i2c_lcd.i2c_lcd(0x27, 1, 2, 1, 0, 4, 5, 6, 7, 3)
        lcd.backLightOn()
    except IOError:
        logging.error("LCD IO Error", exc_info=True)
        lcd = None




    try:        
        #Start GPS polling thread
        gpsp = GpsPoller()
        gpsp.start()
        
        #Start temperature updating thread
        tempthread = TempUpdates()
        tempthread.start()
    
        # If LCD is connected start LCD updating thread. 
        if(lcd != None):
            lcdthread = LcdUpdate()
            lcdthread.start()
        while True: time.sleep(100)
    except:
        raise    
