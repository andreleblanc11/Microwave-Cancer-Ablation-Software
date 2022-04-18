'''
Created on 14.06.2013
LucidControl Analog Input USB Module AI4 implementation
@author: Klaus Ummenhofer
'''

from lucidIo.LucidControl import LucidControl
from lucidIo.Cmd import Cmd
from lucidIo import IoReturn
import struct
from lucidIo.Values import ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4

class LCAI4Mode(object):
    """Module Operation Mode values
    
    This class contains integer values representing the Operation
    Modes. They are supposed to be used with setParamMode and
    getParamMode commands. 
    """
    INACTIVE            = 0x00
    STANDARD            = 0x01
    
class LCAI4DeviceType(object):
    AI_NONE     = (0x0000, "Not identified")
    AI_0_5      = (0x1000, "0 V ~ 5 V")
    AI_0_10     = (0x1001, "0 V ~ 10 V")
    AI_0_12     = (0x1002, "0 V ~ 12 V")
    AI_0_15     = (0x1003, "0 V ~ 15 V")
    AI_0_20     = (0x1004, "0 V ~ 20 V")
    AI_0_24     = (0x1005, "0 V ~ 24 V")
    AI_5_5      = (0x1010, "-5 V ~ 5 V")
    AI_10_10    = (0x1011, "-10 V ~ 10 V")
    AI_12_12    = (0x1012, "-12 V ~ 12 V")
    AI_15_15    = (0x1013, "-15 V ~ 15 V")
    AI_20_20    = (0x1014, "-20 V ~ 20 V")
    AI_24_24    = (0x1015, "-24 V ~ 24 V")
    AI_0_20MA_500 = (0x1110, "0 A ~ 0.02 A")
    
    
class _LCAI4ParamAddress(object):
    VALUE           = 0x1000
    MODE            = 0x1100
    FLAGS           = 0x1101
    NR_SAMPLES      = 0x1112
    OFFSET          = 0x1120



class LucidControlAI4(LucidControl):
    """""LucidControl Analog Input USB Module AI4 class
    """
    
    def getIo(self, channel, value):
        """Get the value or state of an analog input channel.
            
        This method calls the GetIo function of the module and returns
        the value or of the analog input channel.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            value: Value object. Must be either ValueVOS4, ValueVOS2,
                ValueCUS4 or ValueANU2
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance (channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance (value, (ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4)):
            raise TypeError('Expected value as ValueANU2 or ValueVOS2, \
                ValueVOS4 or ValueCUS4 got {}'.format(type(value)))
         
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')

        cmd = Cmd(self.com)
        return cmd.getIo(channel, value)
   


    def getIoGroup(self, channels, values):
        """Get the values of a group of analog input channels.
            
        This method calls the GetIoGroup function of the module and
            returns the values of a group of analog input channels.
        
        Args:
            channels: Tuple with 4 boolean values (one for each channel).
                A channel is only read if the corresponding channel is
                true.
            values: Value objects
                A tuple with 4 value objects. The value objects must be
                either ValueVOS4, ValueVOS2, ValueCUS4 or ValueANU2.
                The function fills the objects with read data.
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channels, tuple):
            raise TypeError('Expected channels as a tuple with 4 channels \
                (bools), got {}'.format(type(channels)))

        if (len(channels) < 4):
            raise TypeError('Expected 4 channels, got {}'.format(len(channels)))
        
        for x in range(4):
            if not isinstance(channels[x], int):
                raise TypeError('Expected channel as bool, got {}'.format(
                    type(channels[x])))

        if not isinstance(values, tuple):
            raise TypeError('Expected values as a tuple with 4 values, got {}'.format(
                type(values)))

        if (len(values) < 4):
            raise TypeError('Expected 4 values, got {}'.format(len(values)))

        for x in range(4):
            if not isinstance(values[x], (ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4)):
                raise TypeError('Expected value as ValueANU2 or ValueVOS2, \
                    ValueVOS4 or ValueCUS4 got {}'.format(type(values[x])))

        cmd = Cmd(self.com)
        return cmd.getIoGroup(channels, values)
    
    
    def getParamValue(self, channel, value):
        """Get the Configuration Parameter "Value" of an analog input channel.
            
        This method calls the GetParam function of the module and returns
            the value of the Configuration Parameter "Value".
        
            The Configuration Parameter "Value" contains the current
            value of the input channel.
        
        It is recommended to call getIo instead of this method.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            value: Value object of ValueANU2 class
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance (channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance(value, ValueANU2):
            raise TypeError('Expected value as ValueANU2, got {}'.format(
                type(value)))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAI4ParamAddress.VALUE, channel, data)
        
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            value._setData(data)
        return ret

    
    def getParamMode(self, channel, mode):
        """Get the Configuration Parameter "Mode" of the analog input channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Mode".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            mode: Operation Mode as a list with one LCAI4Mode integer value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance(mode, list):
            raise TypeError('Expected mode as list, got {}'.format(
                type(mode)))
        
        if len(mode) < 1:
            raise TypeError('Expected mode as list with 1 int, got {}'.format(
                len(mode)))
            
        if not isinstance(mode[0], int):
            raise TypeError('Expected mode[0] as int, got {}'.format(
                type(mode[0])))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     

        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAI4ParamAddress.MODE, channel, data)

        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            if data[0] == LCAI4Mode.INACTIVE:
                mode = LCAI4Mode.INACTIVE
            elif data[0] == LCAI4Mode.STANDARD:
                mode[0] = LCAI4Mode.STANDARD
            else:
                mode[0] = LCAI4Mode.INACTIVE
        return ret


    def setParamModeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Mode" of an analog input channel
            to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Mode" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')   

        cmd = Cmd(self.com)
        return cmd.setParamDefault(_LCAI4ParamAddress.MODE, channel, persistent)

    
    def setParamMode(self, channel, persistent, mode):
        """Set the Configuration Parameter "Mode" of an analog input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Mode".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            mode: Operation Mode as LCAI4Mode integer value
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range    
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))

        if not isinstance(mode, int):
            raise TypeError('Expected mode as int, got {}'.format(
                 type(mode)))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')

        data = bytearray([mode])
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAI4ParamAddress.MODE, channel, persistent, data)

    
    def setParamFlagsDefault(self, channel, persistent):
        """Set the Configuration Parameter "Flags" of an analog input to the
            default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Flags" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')   

        cmd = Cmd(self.com)
        return cmd.setParamDefault(_LCAI4ParamAddress.FLAGS, channel, persistent)


    def getParamScanInterval(self, channel, scanInterval):
        """Get the Configuration Parameter "Scan Interval" of the analog input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Scan Interval".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            scanInterval: Scan Interval as a list containing one integer value
                in milliseconds
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """        
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(scanInterval, list):
            raise TypeError('Expected scanInterval as list, got {}'.format(
                type(scanInterval)))
        
        if len(scanInterval) < 1:
            raise TypeError('Expected scanInterval as list with 1 int, got {}'.format(
                len(scanInterval)))
        
        if not isinstance(scanInterval[0], int):
            raise TypeError('Expected scanInterval[0] as int, got {}'.format(
                type(scanInterval[0])))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAI4ParamAddress.SCAN_INTERVAL, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            scanInterval[0] = struct.unpack("<H", data)[0]
        else:
            scanInterval[0] = 0
        return ret


    
    def setParamScanIntervalDefault(self, channel, persistent):
        """Set the Configuration Parameter "Scan Interval" of an analog
            input to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Scan Interval" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')   
        
        cmd = Cmd(self.com)
        return cmd.setParamDefault(_LCAI4ParamAddress.SCAN_INTERVAL, channel,
            persistent)


    def setParamScanInterval(self, channel, persistent, scanInterval):
        """Set the Configuration Parameter "Scan Interval" of an analog
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Scan Interval".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            scanInterval: Parameter "Scan Interval" in milliseconds.
                Value range 0 ... 0xFFFF
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or scanInterval value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if not isinstance(scanInterval, int):
            raise TypeError('Expected scanInterval as int, got {}'.format(
                type(scanInterval)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        if (scanInterval < 0) | (scanInterval >= pow(2, 16)):
            raise ValueError('Scan Interval out of range')

        data = bytearray(struct.pack("<H", scanInterval))
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAI4ParamAddress.SCAN_INTERVAL, channel,
            persistent, data)
        
        
        
    def getParamNrSamples(self, channel, nrSamples):
        """Get the Configuration Parameter "Number of Samples" of the analog input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Number of Samples".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            nrSamples: Number of Samples as a list containing one integer value
                in milliseconds
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """        
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(nrSamples, list):
            raise TypeError('Expected nrSamples as list, got {}'.format(
                type(nrSamples)))
        
        if len(nrSamples) < 1:
            raise TypeError('Expected nrSamples as list with 1 int, got {}'.format(
                len(nrSamples)))
        
        if not isinstance(nrSamples[0], int):
            raise TypeError('Expected nrSamples[0] as int, got {}'.format(
                type(nrSamples[0])))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAI4ParamAddress.NR_SAMPLES, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            nrSamples[0] = struct.unpack("<H", data)[0]
        else:
            nrSamples[0] = 0
        return ret


    
    def setParamNrSamplesDefault(self, channel, persistent):
        """Set the Configuration Parameter "Number of Samples" of an analog
            input to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Number of Samples" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')   
        
        cmd = Cmd(self.com)
        return cmd.setParamDefault(_LCAI4ParamAddress.NR_SAMPLES, channel,
            persistent)


    def setParamNrSamples(self, channel, persistent, nrSamples):
        """Set the Configuration Parameter "Number of Samples" of an analog
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Number of Samples".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            nrSamples: Parameter "Number of Samples"
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or nrSamples value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if not isinstance(nrSamples, int):
            raise TypeError('Expected nrSamples as int, got {}'.format(
                type(nrSamples)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        if (nrSamples < 0):
            raise ValueError('nrSamples out of range')

        data = bytearray(struct.pack("<H", nrSamples))
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAI4ParamAddress.NR_SAMPLES, channel,
            persistent, data)  
    
    
    def getParamOffset(self, channel, offset):
        """Get the Configuration Parameter "Offset" of the analog input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Offset".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            offset: Offset as a list containing one integer value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """        
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
            
        if not isinstance(offset, list):
            raise TypeError('Expected offset as list, got {}'.format(
                type(offset)))
        
        if len(offset) < 1:
            raise TypeError('Expected offset as list with 1 int, got {}'.format(
                len(offset)))
        
        if not isinstance(offset[0], int):
            raise TypeError('Expected offset[0] as int, got {}'.format(
                type(offset[0])))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAI4ParamAddress.OFFSET, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            offset[0] = struct.unpack("<h", data)[0]
        else:
            offset[0] = 0
        return ret

    
    def setParamOffsetDefault(self, channel, persistent):
        """Set the Configuration Parameter "Offset" of an analog input to the
            default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Offset" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))

        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')   

        cmd = Cmd(self.com)
        return cmd.setParamDefault(_LCAI4ParamAddress.OFFSET, channel, persistent)
    
    
    def setParamOffset(self, channel, persistent, offset):
        """Set the Configuration Parameter "Offset" of an analog
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Offset".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            offset: Parameter "Offset" 
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or offset value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if not isinstance(offset, int):
            raise TypeError('Expected offset as int, got {}'.format(
                type(offset)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        if (offset < (-pow(2, 15))) | (offset >= pow(2, 16)):
            raise ValueError('Offset out of range')

        data = bytearray(struct.pack("<h", offset))
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAI4ParamAddress.OFFSET, channel, persistent,
            data) 
 
    
    def getDeviceTypeName(self):
        """Get device type name as string.
        
        Returns:
            String of the device type name
        
        Raises:
            ValueError: ID data not valid
        """
        if self.id.validData == True:
            if (self.id.deviceType == LCAI4DeviceType.AI_0_5[0]):
                return LCAI4DeviceType.AI_0_5[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_0_10[0]):
                return LCAI4DeviceType.AI_0_10[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_0_12[0]):
                return LCAI4DeviceType.AI_0_12[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_0_15[0]):
                return LCAI4DeviceType.AI_0_15[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_0_20[0]):
                return LCAI4DeviceType.AI_0_20[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_0_24[0]):
                return LCAI4DeviceType.AI_0_24[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_5_5[0]):
                return LCAI4DeviceType.AI_5_5[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_10_10[0]):
                return LCAI4DeviceType.AI_10_10[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_12_12[0]):
                return LCAI4DeviceType.AI_12_12[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_15_15[0]):
                return LCAI4DeviceType.AI_15_15[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_20_20[0]):
                return LCAI4DeviceType.AI_20_20[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_24_24[0]):
                return LCAI4DeviceType.AI_24_24[1]
            elif (self.id.deviceType == LCAI4DeviceType.AI_0_20MA_500[0]):
                return LCAI4DeviceType.AI_0_20MA_500[1]
            else:
                return "Not Identified"
            
    def getDeviceType(self):
        """Get device type.
        
        Returns:
            Device type
        """
        if (self.id.validData == True):
            return self.id.deviceType
        else:
            return LCAI4DeviceType.AI_NONE
        
    
    
    def __init__(self, portName):
        """
        Constructor of LucidControl Analog Input USB Module class
        """
        LucidControl.__init__(self, portName)
        self.nrOfChannels = 4
        