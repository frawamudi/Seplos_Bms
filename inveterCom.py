#!/usr/bin/python3
from configparser import ConfigParser
from logging import warning
from os import read
import re
from requests.structures import CaseInsensitiveDict
import serial
from time import sleep
import binascii
import math
#import serial
import requests
import json
import listMinMax as mx

import mqtt_com 

#import paho.mqtt.client as mqtt

#--------------------------------------------------------------------
# ITEMS | SOI | VER | ADR | CID1 | CID2 | LEN | INFO | CHKSUM | EO1 |
#--------------------------------------------------------------------
# ASCII | 1   |  2  |  2  |  2   |  2   |  4  |  VAR |   4    |  1  |
# BYTE  |     |     |     |      |      |     |      |        |     |
#-------------------------------------------------------------------
#


class seplos:
    #this class implents seplos BMS protocol EMU10xx, 11xx

    #command code CID2
    bmsCommands = {"TeleInfo":"~20004642E00200FD37\r", "TeleCmd":"~20004644E00200FD35\r"}

    bmsTeleInfoCmd = [ 
    "~20004642E00200FD37\r", 
    "~20014642E00201FD35\r", 
    "~20024642E00202FD33\r",
    "~20034642E00203FD31\r",
    "~20044642E00204FD3F\r",
    "~20054642E00205FD3D\r",
    "~20064642E00206FD3B\r",
    "~20074642E00207FD39\r",
    ]

    asciiToBinary = { '0': 0,'1': 1,'2': 2,'3': 3,'4': 4,'5': 5,'6': 6,'7': 7,'8': 8,'9':9,'A':10,'B':11,'C':12,'D':13,'E':14,'F':15 }
    
    

    def __init__(self):
        #test data
        self.bmsTelInfoData = "~20004600A08E00010E0E1C0E160E160E170E170E180E110BFC102E0E1A0E070E0B0E1C0E14060BE40BE60BE50BE50BF10BEC3A9813B604190A3A9B00453A98000103E813BF0000000000000000DF0C$"
        #self.bmsData = "~20004600A08E00010E0EB80ECA0EC70EE10EB70ECD0ED00EC90EA00E9B0EC70EBC0EB20EBB060BF20BE90BF20BF20C100BFB000014A523EF0A9C4000E59C40000103E814AA0000000000000000DE29"
        self.bmsTelCmdData = "~20004600D05E00010E0202020202020202020002020202060000000000000002140011000000020100000100000000000000000001EBA2"
        self.bmsPackVoltage = 0.00
        self.bmsCurrent = 0.00
        self.bmsRatedCapacity = 150
        self.bmsRemainingCapacity = 0.00
        self.bmsPackSOC = 0.00
        self.bmsCellLevelVolages = []
        self.bmsCycles = 1
        self.bmsBusVoltage = 0.00

        #####################################################

        self.bmsStatusFlag = {"stateFlag":0,"currentFlag":0,"lowCellFlag":0,"highCellFlag":0}

    
    def readBms( self, bank ):
        try:
            ser = serial.Serial("/dev/ttyUSB0", 19200, )
            ser.timeout = 2.5
            print(" port opened for communication")
            #ser.write("~20004642E00200FD37\r".encode("ascii"))
            ser.write(self.bmsTeleInfoCmd[bank].encode("ascii"))
            sleep(0.5)     
            received_data = ser.read()              #read serial port
            data_left = ser.inWaiting()             #check for remaining byte
            received_data += ser.read(data_left)
            #self.bmsTelInfoData.strip()
            self.bmsTelInfoData = received_data.decode("ascii")
            print ("TeleInfo:", self.bmsTelInfoData)  #print received data

            '''
            ser.write(self.bmsCommands["TeleCmd"].encode("ascii"))
            sleep(0.5)     
            received_data = ser.read()              #read serial port
            data_left = ser.inWaiting()             #check for remaining byte
            received_data += ser.read(data_left)
            #self.bmsTelInfoData.strip()
            self.bmsTelCmdData = received_data.decode("ascii")
            print ("TeleCmd:", self.bmsTelCmdData)  #print received data
            ser.close()
            return True
            '''            

        except serial.SerialException as var : # var contains details of issue
            print('An Exception Occured')
            print('Exception Details-> ', var)
            ser.close()
            return False


    def extractSeplosCmdData( self, startPointer, pointerRange):
        lengthData = []
        if startPointer > startPointer + 1:
            return lengthData
        for i in range(pointerRange):
            lengthData.append( self.bmsTelCmdData[ i+startPointer ])
        return lengthData

   
    #This function extract data fields from bmsTelInfoData recieved from the bms
    def extractSeplosInfoData( self, startPointer, pointerRange):
        lengthData = []
        if startPointer > startPointer + 1:
            return lengthData
        for i in range(pointerRange):
            lengthData.append( self.bmsTelInfoData[ i+startPointer ])
        return lengthData

    def shiftTwices(self, rawCellData):
        print("Raw Flags:", rawCellData)
        hbyte = self.asciiToBinary[rawCellData[0]]
        lbyte = self.asciiToBinary[rawCellData[1]]


        hbyte = hbyte << 4
        #lbyte = lbyte << 4

        flag = hbyte|lbyte
        return flag


    def calBmsStatusFlags( self):

        #extract bms state
        rawCellData = self.extractSeplosCmdData(105, 2)
        flag = self.shiftTwices( rawCellData )
        self.bmsStatusFlag["stateFlag"] = flag
        print("States Flag:", flag)

        #extract bms current flags
        rawCellData = self.extractSeplosCmdData(85, 2)
        flag = self.shiftTwices( rawCellData )
        self.bmsStatusFlag["currentFlag"] = flag
        print("Current Flag:", flag)


        #extract bms lowCellFlags
        rawCellData = self.extractSeplosCmdData(85, 2)
        flag = self.shiftTwices( rawCellData )
        self.bmsStatusFlag["lowCellFlag"] = flag
        print("Low cell voltage Flag:", flag)


        #extract bms highCellFlag
        rawCellData = self.extractSeplosCmdData(70, 2)
        flag = self.shiftTwices( rawCellData )
        self.bmsStatusFlag["highCellFlag"] = flag
        print("High cell Flag:", flag)



    def calBmsParameters( self, rawCellData, divideBy, typeOfParameter = "None"):
        #print( rawCellData )
        hByte = rawCellData[0] << 12
        #print(rawCellData[0])
        mhByte = rawCellData[1] << 8
        #print(rawCellData[1])
        #print(mhByte)
        mlByte = rawCellData[2] << 4
        #print(rawCellData[2])
        #lByte = rawCellData[3] << 15

        if typeOfParameter == "cellVoltages":
            rawBmsParameter = (hByte | mhByte | mlByte | rawCellData[3])/divideBy
            self.bmsCellLevelVolages.append(rawBmsParameter)
            return True
            #check for parameter types
        elif typeOfParameter == "bmsBankCurrent":

            #the data extracted tells the state of the BMS

            rawCurrentBmsDataInfo = self.extractSeplosCmdData(105, 2)


            print("C/D:", rawCurrentBmsDataInfo)
            if self.asciiToBinary[rawCurrentBmsDataInfo[1]] == 1 and self.asciiToBinary[rawCurrentBmsDataInfo[0]] == 0:
                #rawBmsParameter = ~(hByte )|~(mhByte>>8)|~(mlByte>>4)|rawCellData[3]
                #battery is discharging if this branch execute

                rawBmsParameter = (hByte)|(mhByte)|(mlByte)|rawCellData[3]
                print("beforeDIV", rawBmsParameter)
                #avoid dividing by zero
                if(rawBmsParameter != 0):
                    rawBmsParameter = (~rawBmsParameter) & 0xFFFF
                    rawBmsParameter /=divideBy
                print("C/D", rawBmsParameter)
                self.bmsCurrent = rawBmsParameter
            else:     
                rawBmsParameter = (hByte | mhByte | mlByte | rawCellData[3])/divideBy
                self.bmsCurrent = rawBmsParameter
            return True
        elif typeOfParameter == "bmsBankVoltage":
            rawBmsParameter = (hByte | mhByte | mlByte | rawCellData[3])/divideBy
            self.bmsPackVoltage = rawBmsParameter
            return True        
        elif typeOfParameter == "bmsBankSOC":
            rawBmsParameter = (hByte | mhByte | mlByte | rawCellData[3])/divideBy
            self.bmsPackSOC = rawBmsParameter
            return True
        elif typeOfParameter == "bmsBusVoltage":
            rawBmsParameter = (hByte | mhByte | mlByte | rawCellData[3])/divideBy
            self.bmsBusVoltage = rawBmsParameter
            return True  
        elif typeOfParameter == "bmsCycles":
            rawBmsParameter = (hByte | mhByte | mlByte | rawCellData[3])#/divideBy
            self.bmsCycles = rawBmsParameter
            return True   
        else:
            return False

        #print( cellNo )
        #print(aBinaryCellVoltage)
        #return rawBmsParameter

    
    def extractParameterFields(self,rawBmsData,innerloop, outloop = 0):
        inputList = []
        inputList = rawBmsData.copy()
        #print("list ",inputList)

        if outloop > 0:
            for x in range(outloop):
                cellInByte = []  
                for y in range(innerloop):
                    cellVoltPackets = inputList.pop(0)
                    cellInByte.append(self.asciiToBinary[cellVoltPackets])
                    print("Data > ", cellVoltPackets)

            return cellInByte

        else:
            currentRawByte = []
            #cellInByte = []
            for x in range(innerloop):    
                currentPacket = inputList.pop(0)
                currentRawByte.append(self.asciiToBinary[currentPacket])
            return currentRawByte


    def processAllBmsParameters( self ):

        self.processBmsCellLevelVotage()

        #Process Current
        rawBmsData = self.extractSeplosInfoData( 101, 4)
        cellInByte = self.extractParameterFields(rawBmsData, 4)
        self.calBmsParameters( cellInByte, 100, "bmsBankCurrent")

        #Process BMS Cycles
        rawBmsData = self.extractSeplosInfoData( 127, 4)
        cellInByte = self.extractParameterFields(rawBmsData, 4)
        self.calBmsParameters(cellInByte, 100, "bmsCycles")

        #Process BMS bank and Bus Voltages
        self.processBmsVoltage("bmsBankVoltage")
        self.processBmsVoltage("bmsBusVoltage")

        #Process BMS SOC
        rawBmsData = self.extractSeplosInfoData( 119, 4)
        cellInByte = self.extractParameterFields(rawBmsData, 4)
        self.calBmsParameters(cellInByte, 10, "bmsBankSOC")

        return True


    #this function process cell level votages 
    def processBmsCellLevelVotage( self ):
        self.bmsCellLevelVolages = []
        #find cell level voltages at index 19 to 56( 14s battery bank) with CID2 0x42h
        rawCellLevelBmsData = self.extractSeplosInfoData( 19, 56)
        for x in range(14):
            cellInByte = []
            for y in range(4):
                cellVoltPackets = rawCellLevelBmsData.pop(0) #
                cellInByte.append(self.asciiToBinary[cellVoltPackets ])
            self.calBmsParameters( cellInByte, 1000, "cellVoltages" )#divide by 1000
        return True


    def processBmsCurrent( self ):
        rawCurrentBmsData = self.extractSeplosInfoData( 101, 4)
        currentRawByte = []
        for x in range(4):
            currentPacket = rawCurrentBmsData.pop(0)
            currentRawByte.append(self.asciiToBinary[currentPacket])
        print( currentRawByte)
        self.calBmsParameters( currentRawByte, 100, "bmsBankCurrent")



    def processBmsCycles( self ):
        rawCurrentBmsData = self.extractSeplosInfoData( 127, 4)
        currentRawByte = []
        for x in range(4):
            currentPacket = rawCurrentBmsData.pop(0)
            currentRawByte.append(self.asciiToBinary[currentPacket])
        print( currentRawByte)
        self.calBmsParameters( currentRawByte, 100, "bmsCycles")
        


    def processBmsVoltage( self, totalVoltage = "bmsBankVoltage"):
        if( totalVoltage == "bmsBankVoltage"):
            rawCurrentBmsData = self.extractSeplosInfoData( 105, 4)
        elif( totalVoltage == "bmsBusVoltage"):
            rawCurrentBmsData = self.extractSeplosInfoData( 135, 4)
        else:
            return False

        cellInByte = self.extractParameterFields(rawCurrentBmsData, 4)
        print(totalVoltage, cellInByte)

        if( totalVoltage == "bmsBankVoltage"):
            self.calBmsParameters( cellInByte, 100, "bmsBankVoltage")
            return True
        elif( totalVoltage == "bmsBusVoltage"):
            self.calBmsParameters( cellInByte, 100, "bmsBusVoltage")
            return True
        else:
            return False



    def processBmsSOC( self ):
        rawCurrentBmsData = self.extractSeplosInfoData( 119, 4)
        #rawCurrentBmsData = self.extractSeplosInfoData( 131, 4)
        currentRawByte = []
        for x in range(4):
            currentPacket = rawCurrentBmsData.pop(0)
            currentRawByte.append(self.asciiToBinary[currentPacket])
        print( currentRawByte)
        self.calBmsParameters( currentRawByte, 10, "bmsBankSOC")

    def getBmsCellLevelVoltages( self ):
        return self.bmsCellLevelVolages
    
    def getBmsCurrent( self ):
        return self.bmsCurrent

    def getSeplosdatachecksum( self):
        pass

    def getBmsPackVoltage( self ):
        return self.bmsPackVoltage

    def getBmsBusVoltage( self ):
        return self.bmsBusVoltage

    def getBmsCycles( self ):
        return self.bmsCycles

    def getBmsPackSOC( self ):
        return self.bmsPackSOC

    def getBmsDataLength( self ):
        return len(self.bmsTelInfoData)
    
    def getBmsDataInfoLength( self ):
        return len(self.bmsTelCmdData)


def main(args=None):
    Bms = seplos()

    #REMEMBER TO CHANGE LIST APPEND FUNCTION TO INSERT

    #Read config.ini file
    config_object = ConfigParser()
    config_object.read("config.ini")

    #Get the BMSPARAM
    userinfo = config_object["BMSPARAM"]
    # readBank = int(userinfo["mastercan"])

    data = {
        "Bank": 0,
        #"Rack Voltage": 0.00,
        "Module Voltage": 0.00,
        #"Min cell Voltage": 0.00,
        #"Max cell Voltage": 0.00,
        "Cell Voltages": [],
        "Current": 0.00,
        "SOC":0,
        "BMS Cycles": 0,
        "BMS Range": 0

    }

    client = mqtt_com.connect_mqtt('test.mosquitto.org', 'Sunhive', 'Sunhive', 1883)
    while True: 
        sleep(5)
        readBank = int(userinfo["mastercan"])
        while readBank >= 0 and readBank <= 1: 
            Bms.readBms(readBank)
            #Bms.calBmsStatusFlags()
            Bms.processAllBmsParameters()

            data["Bank"] = readBank
        

            #print("Cell Voltages:", Bms.getBmsCellLevelVoltages())
            data["Cell Voltages"] = Bms.getBmsCellLevelVoltages()

            #print( "Current:" ,Bms.getBmsCurrent())
            data["Current"] = Bms.getBmsCurrent()

            #print( "PackVoltage:", Bms.getBmsPackVoltage())
            data["Module Voltage"] = Bms.getBmsPackVoltage()

            #print( "BusVoltage:", Bms.getBmsBusVoltage())
            data["Pack Voltage"] = Bms.getBmsBusVoltage()

            #print( "Data length:", Bms.getBmsDataLength())
            #print( "Cmd info length:", Bms.getBmsDataInfoLength())

            #print( "SOC:", Bms.getBmsPackSOC())
            data["SOC"] = Bms.getBmsPackSOC()

            #print( "Bms Cycles:", Bms.getBmsCycles())
            data["BMS Cycles"] = Bms.getBmsCycles()

            maxRange = mx.max_check(Bms.bmsCellLevelVolages)
            minRange = mx.min_check(Bms.bmsCellLevelVolages)
            cellRange = (maxRange - minRange)*1000
            #print( "Range:", int(cellRange))
            data["BMS Range"] = int(cellRange)

            print("\n")

            
            msg = json.dumps(data)
            mqtt_com.publish(client, msg)

            #sleep(5)
            readBank -= 1
        


    

    #data type to communicated with mysql server on raspberrypi
    '''
    dictdata = {}
    dictdata["id"] = 1
    dictdata["name"] = "mudi"
    dictdata["capacity"] = 100
    dictdata["voltage"] = bankvolt
    dictdata["current"] = current
    dictdata["soc"] = Bms.getBmsPackSOC()
    '''




    '''
    url = "http://batterystatus.sunhive.com/api/devices/update"

    headers = CaseInsensitiveDict()
    #headers["Content-Type"] = "application/json"

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    data = {
        "deviceID": "SH001",
        "address": "12c Talabi Lagos",
        "size": "3kwh",
        "max_min": "50",
        "numberOfCycle": 11,
        "status": 1
    }
    
    maxRange = mx.max_check(Bms.bmsCellLevelVolages)
    minRange = mx.min_check(Bms.bmsCellLevelVolages)

    cellRange = (maxRange - minRange)*1000
    data["max_min"] = int(cellRange)
    data["numberOfCycle"] = Bms.bmsCycles

    p = json.dumps(data, indent=6)
    print(p)


    resp = requests.post(url, data=p, headers=headers)

    print(resp.status_code)
    '''


    #r = requests.post("http://192.168.1.8/update.php", data=dictdata)
    #print(r.text)
    
    #print(json.dumps(r.text))

if __name__ == '__main__':
    main()

