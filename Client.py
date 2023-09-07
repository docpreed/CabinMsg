#!/usr/bin/python3
import Adafruit_DHT, os
from datetime import date, datetime

# define the gpio pin used on raspberry pi
gpiopin=17

# read temperature and humidity values from dht22 sensor
humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, gpiopin)

# storing formatted temperature/humidity string in tempval variable
tempval = "Temperatur: {:.1f} °C  Luftfeuchtigkeit: {:.1f} %".format(temperature, humidity)

# get current timestamp for reference
current_time = datetime.now().strftime("%H:%M:%S")



# define function to create missing directories
def funcMkDir(path):
        # Check whether the specified path exists or not
        isExist = os.path.exists(path)
        if not isExist:

           # Create a new directory because it does not exist
           os.makedirs(path)

# set current date as today
today = str(date.today())
# get individual values for year, month, date
todayArray = today.split("-")
year = str(todayArray[0])
month = todayArray[1]

# define the path for the logfile to be written to
path = year + "/" + month + "/"

# calling the "create the missing directories" function
funcMkDir(year)
funcMkDir(year + "/" + month)

# write file to destination
with open('/home/pi/' + path + today + '_templog.txt', 'a') as f:
    f.write(current_time + " " + tempval + "\n")
