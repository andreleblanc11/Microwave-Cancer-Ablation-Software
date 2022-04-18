'''
Created on 12.06.2013

@author: Klaus Ummenhofer
'''
from lucidIo.Com import Com
from lucidIo.Cmd import Cmd
from lucidIo.LucidControlId import LucidControlId

class _DeviceClass(object):
    DI4             = (0,       "DIGITAL INPUT 4 CHANNELS")
    DI8             = (0x0010, "DIGITAL INPUT 8 CHANNELS")
    AI4             = (0x0100,  "ANALOG INPUT 4 CHANNELS")
    RI4             = (0x0A00,  "RTD INPUT 4 CHANNELS")
    RI8             = (0x0A10,  "RTD INPUT 8 CHANNELS")
    DO4             = (0x1000,  "DIGITAL OUTPUT 4 CHANNELS")
    DO8             = (0x1010,  "DIGITAL OUTPUT 8 CHANNELS")
    AO4             = (0x1100,  "ANALOG OUTPUT 4 CHANNELS")


class LucidControl(object):
    """
    classdocs
    """

    def getRevisionFw(self):
        if (self.id.validData == True):
            return self.id.revisionFw
        else:
            return 0

    def getRevisionHw(self):
        if (self.id.validData == True):
            return self.id.revisionHw
        else:
            return 0

    def getDeviceClassName(self):
        if (self.id.validData == True):
            if (self.id.deviceClass == _DeviceClass.DI4[0]):
                return _DeviceClass.DI4[1]
            if (self.id.deviceClass == _DeviceClass.DI8[0]):
                return _DeviceClass.DI8[1]
            if (self.id.deviceClass == _DeviceClass.AI4[0]):
                return _DeviceClass.AI4[1]
            if (self.id.deviceClass == _DeviceClass.RI4[0]):
                return _DeviceClass.RI4[1]
            if (self.id.deviceClass == _DeviceClass.RI8[0]):
                return _DeviceClass.RI8[1]
            if (self.id.deviceClass == _DeviceClass.DO4[0]):
                return _DeviceClass.DO4[1]
            if (self.id.deviceClass == _DeviceClass.DO8[0]):
                return _DeviceClass.DO8[1]
            if (self.id.deviceClass == _DeviceClass.AO4[0]):
                return _DeviceClass.AO4[1]
            else:
                return "Device Class invalid"
        else:
            return "Exception"

    def getDeviceSnr(self):
        if (self.id.validData == True):
            return self.id.deviceSnr
        else:
            return 0    


    def identify(self, options):
        
        if not isinstance(options, int):
            raise TypeError('Expected options as int, got {}'.format(
                type(options)))

        if options > 0xFF:
            raise ValueError('Options out of range')

        self.id = LucidControlId() 
        cmd = Cmd(self.com)
        return cmd.identify(options, self.id)


    def open(self):
        return self.com.open()


    def close(self):
        return self.com.close()    


    def __init__(self, portName):
        '''
        Constructor
        '''
        self.portName = portName
        self.com = Com("LucidIo", self.portName)
        self.id = LucidControlId()
        self.nrOfChannels = 0;
