from logging import warning
import serial
from time import sleep
import binascii
import math
#import serial
import requests
import json
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
        self.bmsTemperate = []
        self.bmsCycles = 1
        self.bmsBusVoltage = 0.00

        #####################################################

        self.bmsFaultsStatus = 0 #Alarm event 1
        self.bmsCellVoltageStatus = 0 #Alarm event 2
        self.bmsStatesStatus = 0 #bmsStatus
        self.bmsChargeDischargeStatus = 0 #Alarm event 5
        self.bmsProtectionStatus = 0 #Alarm event 6
        self.bmsCalibrationStatus = 0 #Alarm event 8

    
    def readBms( self ):
        try:
            ser = serial.Serial("/dev/ttyUSB0", 19200, )
            ser.timeout = 2.5
            print(" port opened for communication")
            #ser.write("~20004642E00200FD37\r".encode("ascii"))
            ser.write(self.bmsCommands["TeleInfo"].encode("ascii"))
            sleep(0.5)     
            received_data = ser.read()              #read serial port
            data_left = ser.inWaiting()             #check for remaining byte
            received_data += ser.read(data_left)
            #self.bmsTelInfoData.strip()
            self.bmsTelInfoData = received_data.decode("ascii")
            print ("TeleInfo:", self.bmsTelInfoData)  #print received data

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

        except serial.SerialException as var : # var contains details of issue
            print('An Exception Occured')
            print('Exception Details-> ', var)
            ser.close()
            return False


        """
        except serial.SerialException as e:
            print("Cant open", ser.port)
            print(str(e)) 

            return False

        
        ser = serial.Serial ("/dev/ttyUSB0", 19200)    #Open port with baud rate
        ser.write("~20004642E00200FD37\r".encode("ascii"))

        sleep(0.5)
        received_data = ser.read()              #read serial port
        data_left = ser.inWaiting()             #check for remaining byte
        received_data += ser.read(data_left)
        self.bmsData.strip()
        self.bmsData = received_data.decode("ascii")
        print ("data recieved:", self.bmsData)  #print received data
        ser.close()
        """
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
            rawCurrentBmsDataInfo = self.extractSeplosCmdData(105, 2)

   
            
            print("C/D:", rawCurrentBmsDataInfo)
            if self.asciiToBinary[rawCurrentBmsDataInfo[1]] == 1 and self.asciiToBinary[rawCurrentBmsDataInfo[0]] == 0:
                #rawBmsParameter = ~(hByte )|~(mhByte>>8)|~(mlByte>>4)|rawCellData[3]


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
        return rawBmsParameter
        


    #this function process cell level votages 
    def processBmsCellLevelVotage( self ):
        #clear bmsCellLevelVotage data structure each time this function is called
        #because we using the list.append() which will keep adding to the bmsCellVoltage data
        self.bmsCellLevelVolages = []
        #find cell level voltages at index 19 to 56( 14s battery bank) with CID2 0x42h
        rawCellLevelBmsData = self.extractSeplosInfoData( 19, 56)
        for x in range(14):
            cellInByte = []
            for y in range(4):
                cellVoltPackets = rawCellLevelBmsData.pop(0) #
                cellInByte.append(self.asciiToBinary[cellVoltPackets ])
            # self.bmsCellLevelVolages[ x ]  
            self.calBmsParameters( cellInByte, 1000, "cellVoltages" )#divide by 1000
            #refactory calCellVoltage function to manipulate binary data
            #and do proper data conditioning
            #print(cellInByte)
        return True


    def processBmsCurrent( self ):
        #rawCurrentBmsDataInfo = self.extractSeplosCmdData(107, 2)
        #if self.asciiToBinary[rawCurrentBmsDataInfo[0]] == 1:
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

        currentRawByte = []
        for x in range(4):
            currentPacket = rawCurrentBmsData.pop(0)
            currentRawByte.append(self.asciiToBinary[currentPacket])
        print( currentRawByte)

        if( totalVoltage == "bmsBankVoltage"):
            self.calBmsParameters( currentRawByte, 100, "bmsBankVoltage")
            return True
        elif( totalVoltage == "bmsBusVoltage"):
            self.calBmsParameters( currentRawByte, 100, "bmsBusVoltage")
            return True
        else:
            return False



    def processBmsSOC( self ):
        rawCurrentBmsData = self.extractSeplosInfoData( 119, 4)
        #rawCurrentBmsData = self.extractSeplosData( 131, 4)
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

    def getSeplosdatachecksum( self) :
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

    #length = Bms.extractSeplosData( 19, 56)
    #print( length )
    #print(len(length))
    #cmd = hex ( Bms.bmsData)
    #print( cmd )

    """
    def readBms():
        sleep(0.5)
        received_data = ser.read()              #read serial port
        data_left = ser.inWaiting()             #check for remaining byte
        received_data += ser.read(data_left)
        #print ("data recieved:", received_data)  #print received data
        return received_data
        
    """

    
    #ser = serial.Serial ("/dev/ttyUSB0", 19200)    #Open port with baud rate
    #ser.write("~20004642E00200FD37\r".encode("ascii"))

    #Bms.bmsData = readBms()  
    
    Bms.readBms()
    
    
    Bms.processBmsCellLevelVotage()
    Bms.processBmsCurrent()
    Bms.processBmsVoltage("bmsBusVoltage")
    Bms.processBmsVoltage("bmsBankVoltage")
    Bms.processBmsSOC()
    Bms.processBmsCycles()





    print("Cell Voltages:", Bms.getBmsCellLevelVoltages())
    print( "Current:" ,Bms.getBmsCurrent())
    print( "PackVoltage:", Bms.getBmsPackVoltage())
    print( "BusVoltage:", Bms.getBmsBusVoltage())
    print( "Data length:", Bms.getBmsDataLength())
    print( "Cmd info length:", Bms.getBmsDataInfoLength())
    print( "SOC:", Bms.getBmsPackSOC())
    print( "Bms Cycles:", Bms.getBmsCycles())

    voltages = json.dumps(Bms.getBmsCellLevelVoltages())
    bankvolt = json.dumps(Bms.getBmsPackVoltage())
    current = json.dumps(Bms.getBmsCurrent())

    
    data = {
        "banks": 0,
        "seriesmodules": 14,
        "sent": 1,
        "recieved": 200,
        "modulesfnd": 14,
        "badcrc": 2,
        "ignored": 0,
        "roundtrip": 1000,
        "oos": 0,
        "error": [],
        "warnings": [],
        "voltages": voltages,
        "minvoltages": voltages,
        "maxvoltages": voltages,
        "inittemp": ["23","23", "23","23","23","23","23","23","25","23","23","23","23","21"],
        "exttemp": ["23","23", "23","23","23","23","23","23","25","23","23","23","23","25"],
        "bypass": ["0","0","0","0","0","0","0","0","0","0","0","0","0","0"],
        "bypasshot": ["0","0","0","0","0","0","0","0","0","0","0","0","0","0"],
        "bypasspwm": ["0","0","0","0","0","0","0","0","0","0","0","0","0","0"],
        "bankv": [bankvolt],
        "voltrange": [33],
        "current": [current]
    }
    
    
    b = (json.dumps(data))
    print(b)
    

    dictdata = {}
    dictdata["Current"] = current
    dictdata["Voltage"] = bankvolt
    


    r = requests.post("http://192.168.1.8/monitor2.php", data=dictdata)
    print(r.text)


    # Converting back from ascii to binary 

if __name__ == '__main__':
    main()
