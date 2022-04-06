import serial
from time import sleep

def readBms():
    sleep(0.5)
    received_data = ser.read()              #read serial port
    data_left = ser.inWaiting()             #check for remaining byte
    received_data += ser.read(data_left)
    print ("data recieved:", received_data.decode("ascii"))  #print received data
    #ser.write(received_data)   



ser = serial.Serial ("/dev/ttyUSB0", 19200)    #Open port with baud rate
ser.write("~20004642E00200FD37\r".encode("ascii"))
readBms()
