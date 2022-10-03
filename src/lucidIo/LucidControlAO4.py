'''
Created on 18.01.2014

LucidControl Analog Output USB Module AO4 implementation
@author: Klaus Ummenhofer
'''

from lucidIo.LucidControl import LucidControl
from lucidIo.Cmd import Cmd
from lucidIo import IoReturn
import struct
from lucidIo.Values import ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4

class LCAO4Mode(object):
    """Module Operation Mode values
    
    This class contains integer values representing the Operation
    Modes. They are supposed to be used with setParamMode and
    getParamMode commands. 
    """
    INACTIVE            = 0x00
    STANDARD            = 0x01
    
class LCAO4DeviceType(object):
    AO_NONE     = (0x0000, "Not identified")
    AO_0_5      = (0x1000, "0 V ~ 5 V")
    AO_0_10     = (0x1001, "0 V ~ 10 V")
    AO_0_12     = (0x1002, "0 V ~ 12 V")
    AO_0_15     = (0x1003, "0 V ~ 15 V")
    AO_0_20     = (0x1004, "0 V ~ 20 V")
    AO_0_24     = (0x1005, "0 V ~ 24 V")
    AO_5_5      = (0x1010, "-5 V ~ 5 V")
    AO_10_10    = (0x1011, "-10 V ~ 10 V")
    AO_12_12    = (0x1012, "-12 V ~ 12 V")
    AO_15_15    = (0x1013, "-15 V ~ 15 V")
    AO_20_20    = (0x1014, "-20 V ~ 20 V")
    AO_24_24    = (0x1015, "-24 V ~ 24 V")
    AO_0_20MA   = (0x1100, "0 A ~ 0.02 A")
    AO_4_20MA   = (0x1101, "0.004 A ~ 0x02 A")
    
    
class _LCAO4ParamAddress(object):
    VALUE               = 0x1000
    MODE                = 0x1100
    FLAGS               = 0x1101
    REFRESH_INTERVAL    = 0x1111
    SETUP_TIME          = 0x1112
    REFRESH_TIME        = 0x1113
    OFFSET              = 0x1120

class LucidControlAO4(LucidControl):
    """""LucidControl Analog Output USB Module AO4 class
    """
    
    def getIo(self, channel, value):
        """Get the value or state of an analog output channel.
            
        This method calls the GetIo function of the module and returns
        the current value or of the analog output channel.
        
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
        """Get the values of a group of analog output channels.
            
        This method calls the GetIoGroup function of the module and
            returns the current values of a group of analog output channels.
        
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
            raise TypeError('Expected 4 values, got {}'.format(
                len(values)))

        for x in range(4):
            if not isinstance(values[x], (ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4)):
                raise TypeError('Expected value as ValueANU2 or ValueVOS2, \
                    ValueVOS4 or ValueCUS4 got {}'.format(type(values[x])))

        cmd = Cmd(self.com)
        return cmd.getIoGroup(channels, values)
    
    
    def setIo(self, channel, value):
        """Write the value of one analog output channel.
        
        This method calls the SetIo function of the module and writes
            the value of the analog output channel.
            
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
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
            
        if not isinstance(value, (ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4)):
            raise TypeError('Expected value as ValueANU2 or ValueVOS2, \
                ValueVOS4 or ValueCUS4 got {}'.format(type(value)))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        cmd = Cmd(self.com)
        return cmd.setIo(channel, value)



    def setIoGroup(self, channels, values):
        """Write values of a group of analog output channels.
        
        This method calls the SetIoGroup function of the module and
            writes the values of a group of analog output channels.
            
        Args:
            channels: Tuple with 4 boolean values (one for each channel).
                A channel is only written if the corresponding channel is
                true.
            values: A tuple with 4 value objects.
                The value objects must be either ValueVOS4, ValueVOS2,
                ValueCUS4 or ValueANU2.
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        if not isinstance(channels, tuple):
            raise TypeError('Expected channels as tuple with 4 channels \
                (bools), got {}'.format(type(channels)))
        
        if (len(channels) < 4):
            raise TypeError('Expected 4 channels, got {}'.format(len(channels)))
        
        for x in range(4):
            if not isinstance(channels[x], int):
                raise TypeError('Expected channel as bool, got {}'.format(
                    type(channels[x])))
            
        if not isinstance(values, tuple):
            raise TypeError('Expected values as tuple with 4 values, got {}'.format(
                type(values)))
        
        if (len(values) < 4):
            raise TypeError('Expected 4 values, got {}'.format(
                len(values)))
        
        for x in range(4):
            if not isinstance(values[x], (ValueANU2, ValueVOS2, ValueVOS4, ValueCUS4)):
                raise TypeError('Expected value as ValueANU2 or ValueVOS2, \
                    ValueVOS4 or ValueCUS4 got {}'.format(type(values[x])))
            
        cmd = Cmd(self.com)
        return cmd.setIoGroup(channels, values)
    
    
    def calibrateIo(self, channel, persistent):
        """Calibration of the analog output channels.
            
        This method calls the CalibIo function of the module which executes
            calibration of the analog output channels.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store calibration parameter permanently if true
            
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

        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))

        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')

        cmd = Cmd(self.com)
        return cmd.calibrateIo(channel, 0, persistent)
    
    
    def getParamValue(self, channel, value):
        """Get the Configuration Parameter "Value" of an analog output channel.
            
        This method calls the GetParam function of the module and returns
            the value of the Configuration Parameter "Value".
        
            The Configuration Parameter "Value" contains the current
            value of the analog output channel.
        
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
        ret = cmd.getParam(_LCAO4ParamAddress.VALUE, channel, data)
        
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            value._setData(data)
        return ret

    
    def getParamMode(self, channel, mode):
        """Get the Configuration Parameter "Mode" of the analog output channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Mode".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            mode: Operation Mode as a list with one LCAO4Mode integer value
            
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
        ret = cmd.getParam(_LCAO4ParamAddress.MODE, channel, data)

        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            if data[0] == LCAO4Mode.INACTIVE:
                mode = LCAO4Mode.INACTIVE
            elif data[0] == LCAO4Mode.STANDARD:
                mode[0] = LCAO4Mode.STANDARD
            else:
                mode[0] = LCAO4Mode.INACTIVE
        return ret


    def setParamModeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Mode" of an analog output channel
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
        return cmd.setParamDefault(_LCAO4ParamAddress.MODE, channel, persistent)

    
    def setParamMode(self, channel, persistent, mode):
        """Set the Configuration Parameter "Mode" of an analog output channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Mode".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            mode: Operation Mode as LCAO4Mode integer value
        
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
        return cmd.setParam(_LCAO4ParamAddress.MODE, channel, persistent, data)

    
    def setParamFlagsDefault(self, channel, persistent):
        """Set the Configuration Parameter "Flags" of an analog output to the
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
        return cmd.setParamDefault(_LCAO4ParamAddress.FLAGS, channel, persistent)


    def getParamRefreshInterval(self, channel, refreshInterval):
        """Get the Configuration Parameter "Refresh Interval" of the analog output
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Refresh Interval".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            refreshInterval: Refresh Interval as a list containing one integer value
                in microseconds
            
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
        
        if not isinstance(refreshInterval, list):
            raise TypeError('Expected  refreshInterval as list, got {}'.format(
                type(refreshInterval)))
        
        if len(refreshInterval) < 1:
            raise TypeError('Expected refreshInterval as list with 1 int, got {}'.format(
                len(refreshInterval)))
        
        if not isinstance(refreshInterval[0], int):
            raise TypeError('Expected refreshInterval[0] as int, got {}'.format(
                type(refreshInterval[0])))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAO4ParamAddress.REFRESH_INTERVAL, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            refreshInterval[0] = struct.unpack("<I", data)[0]
        else:
            refreshInterval[0] = 0
        return ret


    
    def setParamRefreshIntervalDefault(self, channel, persistent):
        """Set the Configuration Parameter "Refresh Interval" of an analog
            output to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Refresh Interval" to the default value.
        
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
        return cmd.setParamDefault(_LCAO4ParamAddress.REFRESH_INTERVAL, channel,
            persistent)


    def setParamRefreshInterval(self, channel, persistent, refreshInterval):
        """Set the Configuration Parameter "Refresh Interval" of an analog
            output channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Refresh Interval".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            refreshInterval: Parameter "Refresh Interval" in microseconds.
                Value must be positive.
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or refreshInterval value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if not isinstance(refreshInterval, int):
            raise TypeError('Expected refreshInterval as int, got {}'.format(
                type(refreshInterval)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        if (refreshInterval < 0) | (refreshInterval >= pow(2, 32)):
            raise ValueError('Refresh Interval out of range')

        data = bytearray(struct.pack("<I", refreshInterval))
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAO4ParamAddress.REFRESH_INTERVAL, channel,
            persistent, data) 
        
        
    def getParamSetupTime(self, channel, setupTime):
        """Get the Configuration Parameter "Setup Time" of the analog output
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Setup Time".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            setupTime: Setup Time as a list containing one integer value
                in microseconds.
            
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
        
        if not isinstance(setupTime, list):
            raise TypeError('Expected  setupTime as list, got {}'.format(
                type(setupTime)))
        
        if len(setupTime) < 1:
            raise TypeError('Expected setupTime as list with 1 int, got {}'.format(
                len(setupTime)))
        
        if not isinstance(setupTime[0], int):
            raise TypeError('Expected setupTime[0] as int, got {}'.format(
                type(setupTime[0])))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAO4ParamAddress.SETUP_TIME, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            setupTime[0] = struct.unpack("<I", data)[0]
        else:
            setupTime[0] = 0
        return ret


    
    def setParamSetupTimeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Setup Time" of an analog
            output to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Setup Time" to the default value.
        
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
        return cmd.setParamDefault(_LCAO4ParamAddress.SETUP_TIME, channel,
            persistent)


    def setParamSetupTime(self, channel, persistent, setupTime):
        """Set the Configuration Parameter "Setup Time" of an analog
            output channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Setup Time".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            setupTime: Parameter "Setup Time" in microseconds.
                Value must be positive.
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or setupTime value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if not isinstance(setupTime, int):
            raise TypeError('Expected setupTime as int, got {}'.format(
                type(setupTime)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        if (setupTime < 0) | (setupTime >= pow(2, 32)):
            raise ValueError('setupTime out of range')

        data = bytearray(struct.pack("<I", setupTime))
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAO4ParamAddress.SETUP_TIME, channel,
            persistent, data) 

        
    def getParamRefreshTime(self, channel, refreshTime):
        """Get the Configuration Parameter "Refresh Time" of the analog output
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Refresh Time".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            refreshTime: Refresh Time as a list containing one integer value
                in microseconds.
            
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
        
        if not isinstance(refreshTime, list):
            raise TypeError('Expected refreshTime as list, got {}'.format(
                type(refreshTime)))
        
        if len(refreshTime) < 1:
            raise TypeError('Expected refreshTime as list with 1 int, got {}'.format(
                len(refreshTime)))
        
        if not isinstance(refreshTime[0], int):
            raise TypeError('Expected refreshTime[0] as int, got {}'.format(
                type(refreshTime[0])))
            
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')     
        
        data = bytearray()
        cmd = Cmd(self.com)
        ret = cmd.getParam(_LCAO4ParamAddress.REFRESH_TIME, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            refreshTime[0] = struct.unpack("<I", data)[0]
        else:
            refreshTime[0] = 0
        return ret


    
    def setParamRefreshTimeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Refresh Time" of an analog
            output to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Refresh Time" to the default value.
        
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
        return cmd.setParamDefault(_LCAO4ParamAddress.REFRESH_TIME, channel,
            persistent)


    def setParamRefreshTime(self, channel, persistent, refreshTime):
        """Set the Configuration Parameter "Refresh Time" of an analog
            output channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Refresh Time".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            refreshTime: Parameter "Refresh Time" in microseconds.
                Value must be positive.
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or setupTime value is out of range
        """
        if not isinstance(channel, int):
            raise TypeError('Expected channel as int, got {}'.format(
                type(channel)))
        
        if not isinstance(persistent, bool):
            raise TypeError('Expected persistent as bool, got {}'.format(
                type(persistent)))
        
        if not isinstance(refreshTime, int):
            raise TypeError('Expected refreshTime as int, got {}'.format(
                type(refreshTime)))
        
        if (channel >= self.nrOfChannels):
            raise ValueError('Channel out of range')
        
        if (refreshTime < 0) | (refreshTime >= pow(2, 32)):
            raise ValueError('refreshTime out of range')

        data = bytearray(struct.pack("<I", refreshTime))
        cmd = Cmd(self.com)
        return cmd.setParam(_LCAO4ParamAddress.REFRESH_TIME, channel,
            persistent, data) 
    
    
    def getParamOffset(self, channel, offset):
        """Get the Configuration Parameter "Offset" of the analog output
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Offset".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            offset: Offset as a list containing one integer value
                representing the offset voltage in millivolt.
            
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
        ret = cmd.getParam(_LCAO4ParamAddress.OFFSET, channel, data)
    
        if ret == IoReturn.IoReturn.IO_RETURN_OK:
            offset[0] = struct.unpack("<h", data)[0]
        else:
            offset[0] = 0
        return ret

    
    def setParamOffsetDefault(self, channel, persistent):
        """Set the Configuration Parameter "Offset" of an analog output to the
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
        return cmd.setParamDefault(_LCAO4ParamAddress.OFFSET, channel, persistent)
    
    
    def setParamOffset(self, channel, persistent, offset):
        """Set the Configuration Parameter "Offset" of an analog
            output channel.
            
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
        return cmd.setParam(_LCAO4ParamAddress.OFFSET, channel, persistent,
            data) 
 
    def getDeviceTypeName(self):
        """Get device type name as string.
        
        Returns:
            String of the device type name
        """
        if self.id.validData == True:
            if (self.id.deviceType == LCAO4DeviceType.AO_0_5[0]):
                return LCAO4DeviceType.AO_0_5[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_0_10[0]):
                return LCAO4DeviceType.AO_0_10[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_0_12[0]):
                return LCAO4DeviceType.AO_0_12[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_0_15[0]):
                return LCAO4DeviceType.AO_0_15[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_0_20[0]):
                return LCAO4DeviceType.AO_0_20[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_0_24[0]):
                return LCAO4DeviceType.AO_0_24[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_5_5[0]):
                return LCAO4DeviceType.AO_5_5[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_10_10[0]):
                return LCAO4DeviceType.AO_10_10[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_12_12[0]):
                return LCAO4DeviceType.AO_12_12[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_15_15[0]):
                return LCAO4DeviceType.AO_15_15[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_20_20[0]):
                return LCAO4DeviceType.AO_20_20[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_24_24[0]):
                return LCAO4DeviceType.AO_24_24[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_0_20MA[0]):
                return LCAO4DeviceType.AO_0_20MA[1]
            elif (self.id.deviceType == LCAO4DeviceType.AO_4_20MA[0]):
                return LCAO4DeviceType.AO_4_20MA[1]
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
            return LCAO4DeviceType.AO_NONE
        
    
    def __init__(self, portName):
        """
        Constructor of LucidControl Analog Output USB Module class
        """
        LucidControl.__init__(self, portName)
        self.nrOfChannels = 4
        