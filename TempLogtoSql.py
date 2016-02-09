#import webiopi
import os
#os.system("export QUICK2WIRE_API_HOME=~/temperature/quick2wire-python-api")
#os.system("export PYTHONPATH=$PYTHONPATH:$QUICK2WIRE_API_HOME")
#os.system("export MPU6050_PATH=~/temperature/MPU6050")
#os.system("export PYTHONPATH=$PYTHONPATH:$MPU6050_PATH")
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='./Loggingonly.log', level=logging.DEBUG)
import datetime
import pymysql.cursors
import RPi.GPIO as GPIO
import time
from time import mktime
from datetime import timedelta
import threading
import sys
#import dateutil.parser
import math
import signal
import Adafruit_BMP.BMP085 as BMP085
import collections

#from i2clibraries import i2c_lcd


from _ctypes import addressof


#signal.signal(signal.SIGINT, signal_handler)

units = "c"

AmbientTemp = 0








tmp = None



def signal_quitting(signal, frame):
    global gpsp
    logging.info("Received Sigint, killing threads and waiting for join. ")
    tempthread.running = False

    tempthread.join(2)
    logging.info("temperature updating thread killed, quitting")
    logging.info("all threads killed, quitting")
    logging.info('You pressed Ctrl+C!')    
    sys.exit(0)    


def logTemplineDB(location, temp):    
    try:
        connection = pymysql.connect(host='192.168.1.104', user='monitor', passwd='password', db='temps', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            cursor.execute ("INSERT INTO tempdat values(NOW(), NOW(), %s, %s, 'empty')", (location, temp))
        connection.commit()
        logging.debug("logTempLineDB() Rows logged: %s" % cursor.rowcount)
        connection.close()
    except:
        logging.error("logTempLineDB Temperature Logging exception Error ", exc_info=True)



def UpdateTemps():
    global AmbientTemp
    global tmp
  
    
    if(tmp != None):
        try:
            AmbientTemp = tmp.read_temperature()
            logTemplineDB("garage", AmbientTemp)
        except:
            logging.error("UpdateTemps() Ambient Temp Read Error: ", exc_info=True)



 
 
 
class TempUpdates(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.current_value = None
        self.running = True #setting the thread running to true 
        
        
    def run(self):                 
        while self.running:
            UpdateTemps()
            time.sleep(300)
            
 
 
if __name__ == "__main__":

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

        
        tempthread = TempUpdates()
        tempthread.start()
   

    except:
        raise    
