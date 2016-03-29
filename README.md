# LoggingOnly

Program started off as a simple raspberry pi applicaion to save temperature measurements and GPS coordinates to a mysql database for later analysis. The purpose was to connect it to a cylinder head temperature sensor on my motorcycle and see how the temp changes over the course of a ride. Gradually, more sensors and an LCD display were added.
Code is rough, but parts of it might be helpful for reference. 


# Requires/Credits
- https://github.com/adafruit/Adafruit_Python_BMP
- http://think-bowl.com/raspberry-pi/installing-the-think-bowl-i2c-libraries-for-python/
- https://github.com/PyMySQL/PyMySQL
- http://blog.pistuffing.co.uk/python-code-for-i2c-mpu6050-pwm-and-pid/
 
# Description
The program contains several small threads

The gpsp thread polls the GPSD client for new gpx fixes. If 2 seconds have passed the point is logged to the mysql database and parsed into a string for display on the LCD

The tempthread thread periodically reads from the MAX6675 sensor for engine temp and the BMP085 sensor for ambient temp. It logs them to mysql and puts them into a string for display. 

The lcdthread thread updates the LCD screen with the strings being populated by the other threads. 
