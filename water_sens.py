#       ***SETUP***

# Import necessary libraries
import time
import datetime
import RPi.GPIO as GPIO
import Adafruit_MCP3008
import json
from ftplib import FTP


# GPIO pin setup
GPIO.setmode(GPIO.BCM)

valve = 21
servo = 26
TRIG = 20
ECHO = 16

GPIO.setup(valve, GPIO.OUT)
GPIO.setup(servo, GPIO.OUT)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.output(valve,0)

# Servo pwm setup
p = GPIO.PWM(26, 50)
plantAngle = [6.3, 6.8, 7.4, 7.9, 8.5, 9.05, 9.6, 10.1, 10.6]
p.start(plantAngle[0])

# Valve test

def valveTest():
    while True:
        GPIO.output(valve, 1)
        time.sleep(4)
        GPIO.output(valve, 0)
        time.sleep(4)
#valveTest()

# Servo calibration test
def servoTest():
    print("Testing servo")
    p.ChangeDutyCycle(plantAngle[0])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[1])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[2])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[3])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[4])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[5])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[6])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[7])
    time.sleep(4)
    p.ChangeDutyCycle(plantAngle[8])
    time.sleep(4)

#servoTest()


# Software SPI configuration / senspor values:
CLK  = 18
MISO = 23
MOSI = 24
CS   = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
values = [0]*8

# Define and initialize an array that keeps track of the last time plants were watered
lastWatered = [0] * 8
lastLogUpdate = 0
waterLevel = 0

ftp = FTP('158.69.218.29')
ftp.login('zach','xdX6eR')
ftp.retrbinary('RETR plants.json', open('plants.json', 'wb').write)

log = json.loads(open('plants.json', 'r').read())

waterLevel = log[u'garden'][u'waterLevel']
lastLogUpdate = log[u'garden'][u'lastUpdate']

for i in range(0,8):
    lastWatered[i] = log[u'garden'][u'plants'][i][u'lastWatered']
ftp.quit()


#       *** SECONDARY METHODS ***

# log update method
def updateLog():
    ftp = FTP('158.69.218.29')
    ftp.login('zach','xdX6eR')
    ftp.retrbinary('RETR plants.json', open('plants.json', 'wb').write)

    log = json.loads(open('plants.json', 'r').read())
    log[u'garden'][u'waterLevel']=waterLevel
    log[u'garden'][u'lastUpdate']=time.time()
    f = open('water.log', 'a')
    f.write(currentTime + ": ")
    f.write("updating log\n")
    f.close()

     for i in range(0,8):
         log[u'garden'][u'plants'][i][u'lastWatered']=lastWatered[i]
         log[u'garden'][u'plants'][i][u'status']=values[i]
    open('plants.json','w').write(json.dumps(log))

    ftp.storbinary('STOR plants.json', open('plants.json', 'rb'))
    ftp.quit()
    lastLogUpdate = time.time()

# plant watering method
def waterPlant(plantPos, secs = 5.0):
#    if True:
    if time.time() - lastWatered[plantPos] > 900:
        print("Watering plant " + str(plantPos) + "\n")
        print("At angle " + str(plantAngle[plantPos]) + "\n")
        f = open('water.log', 'a')
        f.write(currentTime + ": ")
        f.write("wateringPlant " + str(plantPos) + "\n")
        f.close()
        p.ChangeDutyCycle(plantAngle[plantPos])
        time.sleep(4)
        GPIO.output(valve, 1)
        time.sleep(secs)
        lastWatered[plantPos] = time.time()
        GPIO.output(valve, 0)


# log script restart
f = open('water.log', 'a')
f.write('\nScript rebooted at: ' + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + "\n")
f.write('Initial sensor values: ')
f.write("0: " + str(mcp.read_adc(0)) + " - 1: " + str(mcp.read_adc(1)) + " - 2: " + str(mcp.read_adc(2)) + " - 3: " + str(mcp.read_adc(3)) + " - 4: " + str(mcp.read_adc(4)) + " - 5: " + str(mcp.read_adc(5)) + " - 6: " + str(mcp.read_adc(6)) $
f.close()

currentTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

#updateLog()

#       *** MAIN METHOD ***

# Main program loop.
while True:

    # update time
    currentTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    # if log has not been updated in more than 15 mins aka 900 seconds, update it
    if time.time() - lastLogUpdate > 60:
        updateLog()

#    print "Distance measurement in progress"

    GPIO.output(TRIG, False)                 #Set TRIG as LOW
#    print "Waitng For Sensor To Settle"
    time.sleep(2)                            #Delay of 2 seconds

    GPIO.output(TRIG, True)                  #Set TRIG as HIGH
    time.sleep(0.00001)                      #Delay of 0.00001 seconds
    GPIO.output(TRIG, False)                 #Set TRIG as LOW

    pulse_start = time.time()
    pulse_end = time.time()

    while GPIO.input(ECHO)==0:               #Check whether the ECHO is LOW
        pulse_start = time.time()              #Saves the last known time of LOW pulse

    while GPIO.input(ECHO)==1:               #Check whether the ECHO is HIGH
        pulse_end = time.time()                #Saves the last known time of HIGH pulse

    pulse_duration = pulse_end - pulse_start #Get pulse duration to a variable

    distance = pulse_duration * 17150        #Multiply pulse duration by 17150 to get distance
    distance = round(distance, 2)            #Round to two decimal points

    if distance > 2 and distance < 400:      #Check whether the distance is within range
        print "Distance:",distance - 0.5,"cm"  #Print distance with 0.5 cm calibration
        waterLevel = distance
    else:
        print "Out Of Range"                   #display out of range

    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc(i)
        print(str(values[i]) + " - "),
        if values[i]<650 and values[i]>100:
            waterPlant(i)

#    print(" ")

    # Close the valve just in case
    GPIO.output(valve, 0)

#    updateLog()

    # Pause for half a second.
    time.sleep(0.5)
