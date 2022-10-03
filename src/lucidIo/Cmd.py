'''
Created on 10.06.2013

@author: Klaus Ummenhofer
'''
from lucidIo import IoReturn
import struct

class _Opc(object):
    OPC_SETIO           = 0x40
    OPC_SETIO_GROUP     = 0x42
    OPC_GETIO           = 0x46
    OPC_GETIO_GROUP     = 0x48 
    OPC_CALIBIO         = 0x52 
    OPC_GETID           = 0xC0 
    OPC_SETPARAM        = 0xA0 
    OPC_GETPARAM        = 0xA2  
  
class TxCmd(object):
    '''
    classdocs
    '''
    def __init__(self, com):
        self.data = bytearray()
        self.com = com
    
    def initCmd(self, opc, p1, p2):      
        self.opc = opc
        self.p1 = p1
        self.p2 = p2
        self.p1a = 0
        self.useP1a = False
        
    def initCmdA(self, opc, p1, p1a, p2):
        self.opc = opc
        self.p1 = p1
        self.p1a = p1a
        self.p2 = p2 
        self.useP1a = True
        
    
    def initCmdData(self, opc, p1, p2, data):
        self.initCmd(opc, p1, p2)
        self.data = data
        
    def initCmdDataA(self, opc, p1, p1a, p2, data):
        self.initCmdA(opc, p1, p1a, p2)
        self.data = data
        

    def getTxData(self):
        if self.useP1a == True:
            retData = bytearray([self.opc, self.p1, self.p1a, self.p2])
        else:
            retData = bytearray([self.opc, self.p1, self.p2])

        retData.append(len(self.data))
        retData += self.data 
        return retData
        
    
    def transmit(self):
        return self.com.write(self.getTxData())
        pass
   

class RxCmd(object):
    '''
    classdocs
    '''
    def __init__(self, com):
        '''
        Constructor
        '''
        self.status = 0
        self.com = com
        self.data = bytearray()
        pass  
    
    def receive(self):
        ret = 0
               
        header = bytearray(2)
        headerLen = 2
        ioRet = self.com.read(header, headerLen)
        
        if (ioRet == True):
            ret += 2
            self.status = header[0]
            
            if (self.status == IoReturn.IoReturn.IO_RETURN_OK):
                if(header[1] != 0):
                    expectedBytes = header[1]
                    self.data = bytearray(expectedBytes);
                    ioRet = self.com.read(self.data, expectedBytes)
                    
                    if (ioRet == True):
                        ret += expectedBytes
                    else:
                        ret = -1
        else:
            ret = -1
        return ret
        

class Cmd(object):
    def getIo(self, channel, value):
        
        valueToken = value._valueType;
        
        txCmd = TxCmd(self.com)
        txCmd.initCmd(_Opc.OPC_GETIO, channel, valueToken)
        
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        ret = rxCmd.status
        
        if (ret == IoReturn.IoReturn.IO_RETURN_OK):
            value._setData(rxCmd.data)
            
        return ret
        
    
    def getIoGroup(self, channels, values):
        channelMask = 0
        valueToken = values[0]._valueType
        # Build Channel Mask and count values
        for i in range(0, len(channels)):
            if (channels[i] == True):
                channelMask |= (1 << i)
                
        p1 = channelMask & 0x7F     # Channels 0-6 in P1
        
        if (channelMask > 0x7F):
            p1 |= 0x80
            p1a = (channelMask >> 7) & 0x7F
            txCmd = TxCmd(self.com)
            txCmd.initCmdA(_Opc.OPC_GETIO_GROUP, p1, p1a, valueToken)
        else:
            txCmd = TxCmd(self.com)
            txCmd.initCmd(_Opc.OPC_GETIO_GROUP, p1, valueToken)
        
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        ret = rxCmd.status
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            j = 0
            for i in range(0, len(channels)):
                if channels[i] == False:
                    continue
                
                values[i]._channel = i
                values[i]._setData(
                    rxCmd.data[values[i]._size * j:values[i]._size * (j + 1)])
                
                # Marker in data frame
                j = j + 1
        return ret
        
    
    def setIo(self, channel, value):
        data = bytearray()
        valueToken = value._valueType
        
        value._getData(data)
        
        txCmd = TxCmd(self.com)
        txCmd.initCmdData(_Opc.OPC_SETIO, channel, valueToken, data)
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        ret = rxCmd.status
        return ret

    
    def setIoGroup(self, channels, values):
        valueToken = values[0]._valueType

        channelMask = 0
        for i in range(0, len(channels)):
            if channels[i] == True:
                channelMask |= (1 << i)
                
        data = bytearray()
        
        # Fill data
        for i in range(0, len(channels)):
            if channels[i] == True:
                values[i]._getData(data)

        p1 = channelMask & 0x7F     # Channels 0-6 in P1
        
        if (channelMask > 0x7F):
            p1 |= 0x80
            p1a = (channelMask >> 7) & 0x7F
            txCmd = TxCmd(self.com)
            txCmd.initCmdDataA(_Opc.OPC_SETIO_GROUP, p1, p1a, valueToken, data)
        else:
            txCmd = TxCmd(self.com)
            txCmd.initCmdData(_Opc.OPC_SETIO_GROUP, p1, valueToken, data)

        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        return rxCmd.status

    
    def getParam(self, pAddress, channel, data):
        
        d = bytearray()
        
        # Get Parameter Address
        d += bytearray(struct.pack("<H", pAddress))
        
        txCmd = TxCmd(self.com)
        txCmd.initCmdData(_Opc.OPC_GETPARAM, channel, 0, d)
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        ret = rxCmd.status
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            data += rxCmd.data
            
        return ret
            
    
    def setParam(self, pAddress, channel, persistent, data):
        
        d = bytearray()
        p2 = 0
        
        if persistent == True:
            p2 |= 0x80
            
        # Get Parameter Address
        d += bytearray(struct.pack('<H', pAddress))
        
        # Get Data for transmission
        d += data
        
        txCmd = TxCmd(self.com)
        txCmd.initCmdData(_Opc.OPC_SETPARAM, channel, p2, d)
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        return rxCmd.status
    
    def setParamDefault(self, pAddress, channel, persistent):
        
        d = bytearray()

        # Set Default Flag      
        p2 = 0x01
        
        if persistent == True:
            p2 |= 0x80
        
        # Get Parameter Address
        d += bytearray(struct.pack("<H", pAddress))
        
        txCmd = TxCmd(self.com)
        txCmd.initCmdData(_Opc.OPC_SETPARAM, channel, p2, d)
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        return rxCmd.status
    

    def identify(self, options, lId):
        txCmd = TxCmd(self.com)
        txCmd.initCmd(_Opc.OPC_GETID, 0, options)
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        
        ret = rxCmd.status
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            lId.revisionFw = struct.unpack("<H", rxCmd.data[0:2])[0]
            lId.revisionHw = struct.unpack("B", rxCmd.data[2:3])[0]
            lId.deviceClass = struct.unpack("<H", rxCmd.data[3:5])[0]
            lId.deviceType = struct.unpack("<H", rxCmd.data[5:7])[0]
            lId.deviceSnr = struct.unpack("<I", rxCmd.data[7:11])[0]
            lId.validData = True
            
        return ret
        

    
    def calibrateIo(self, channel, options, persistent):
        
        if persistent == True:
            options |= 0x80
            
        txCmd = TxCmd(self.com)
        txCmd.initCmd(_Opc.OPC_CALIBIO, channel, options)
        txCmd.transmit()
        
        rxCmd = RxCmd(self.com)
        rxCmd.receive()
        return rxCmd.status
    
    def __init__(self, com):
        self.com = com