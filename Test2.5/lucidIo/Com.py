'''
Created on 10.06.2013

@author: Klaus Ummenhofer
'''

import serial

class Com(object):
    '''
    classdocs
    '''
    app = ""
    portName =""
    serial = None
    bOpen = False
    
    def write(self, data):
        self.serial.write(data)
    
    def read(self, data, length):
        n = self.serial.readinto(data)
        
        # Not enough data received, timeout
        if (n != len(data)):
            return False
        
        return True
    
    def isOpened(self):
        return self.bOpen
    

    def open(self):
        self.serial.port = self.portName
        self.serial.baudrate = 9600
        self.serial.timeout = 1000
        self.serial.open()
        self.bOpen = True
        
        
    def close(self):
        self.serial.close()
        self.bOpen = False
        
        

    def __init__(self, app, portName):
        '''
        Constructor
        '''
        self.app = app
        self.portName = portName
        self.bOpen = False
        self.serial = serial.Serial()
        