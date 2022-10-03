'''
Created on 28.07.2018
LucidControl RTD Input USB Module RT8 implementation
@author: Klaus Ummenhofer
'''
from lucidIo.LucidControl import LucidControl
from lucidIo.LucidControlRT import LucidControlRT


class LucidControlRT8(LucidControlRT):
    """""LucidControl RTD Input USB Module RT8 class
    """
    
    def getIo(self, channel, value):
        """Get the value or state of a RTD input channel.
            
        This method calls the GetIo function of the module and returns
        the value or of the RTD input channel.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            value: Value object. Must be either ValueTMS4, ValueTMS2 or
                ValueRMU2
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).getIo(channel, value)

    
    def getIoGroup(self, channels, values):
        """Get the values of a group of RTD input channels.
            
        This method calls the GetIoGroup function of the module and
            returns the values of a group of RTD input channels.
        
        Args:
            channels: Tuple with 8 boolean values (one for each channel).
                A channel is only read if the corresponding channel is
                true.
            values: Value objects
                A tuple with 8 value objects. The value objects must be
                either ValueTMS4, ValueTMS2 or ValueRMU2. The function fills
                the objects with read data.
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).getIoGroup(channels, values)
    
    
    def getParamValue(self, channel, value):
        """Get the Configuration Parameter "Value" of a RTD input channel.
            
        This method calls the GetParam function of the module and returns
            the value of the Configuration Parameter "Value".
        
            The Configuration Parameter "Value" contains the current
            value of the input channel.
        
        It is recommended to call getIo instead of this method.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            value: Value object of ValueRMU2 class
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).getParamValue(channel, value)

    
    def getParamMode(self, channel, mode):
        """Get the Configuration Parameter "Mode" of the RTD input channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Mode".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            mode: Operation Mode as a list with one LCRTMode integer value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).getParamMode(channel, mode)


    def setParamModeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Mode" of a RTD input channel
            to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Mode" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).setParamModeDefault(channel, persistent)

    
    def setParamMode(self, channel, persistent, mode):
        """Set the Configuration Parameter "Mode" of a RTD input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Mode".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            mode: Operation Mode as LCRTMode integer value
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range    
        """
        return super(LucidControlRT8, self).setParamMode(channel, persistent, mode)

    
    def setParamFlagsDefault(self, channel, persistent):
        """Set the Configuration Parameter "Flags" of a RTD input to the
            default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Flags" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).setParamFlagsDefault(channel, persistent)


    def getParamScanInterval(self, channel, scanInterval):
        """Get the Configuration Parameter "Scan Interval" of the RTD input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Scan Interval".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            scanInterval: Scan Interval as a list containing one integer value
                in milliseconds
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """  
        return super(LucidControlRT8, self).getParamScanInterval(channel, scanInterval)      

    
    def setParamScanIntervalDefault(self, channel, persistent):
        """Set the Configuration Parameter "Scan Interval" of a RTD input to the
            default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Scan Interval" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).setParamScanIntervalDefault(channel, persistent)


    def setParamScanInterval(self, channel, persistent, scanInterval):
        """Set the Configuration Parameter "Scan Interval" of a RTD
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Scan Interval".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
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
        return super(LucidControlRT8, self).setParamScanInterval(channel, persistent, scanInterval)
 
 
    def getParamSetupTime(self, channel, setupTime):
        """Get the Configuration Parameter "Setup Time" of the RTD input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Setup Time".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            setupTime: Setup Time as a list containing one integer value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """   
        return super(LucidControlRT8, self).getParamSetupTime(channel, setupTime)     

    
    def setParamSetupTimeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Setup Time" of a RTD input to the
            default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Setup Time" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).setParamSetupTimeDefault(channel, persistent)


    def setParamSetupTime(self, channel, persistent, setupTime):
        """Set the Configuration Parameter "Setup Time" of a RTD
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Setup Time".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            setupTime: Parameter "Setup Time" in milliseconds.
                Value range 0 ... 0xFFFF
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or setupTime value is out of range
        """
        return super(LucidControlRT8, self).setParamSetupTime(channel, persistent, setupTime)
 
 
    def getParamOffset(self, channel, offset):
        """Get the Configuration Parameter "Offset" of the RTD input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Offset".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            offset: Offset as a list containing one integer value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """      
        return super(LucidControlRT8, self).getParamOffset(channel, offset)  

    
    def setParamOffsetDefault(self, channel, persistent):
        """Set the Configuration Parameter "Offset" of a RTD input to the
            default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Offset" to the default value.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlRT8, self).setParamOffsetDefault(channel, persistent)
    
    
    def setParamOffset(self, channel, persistent, offset):
        """Set the Configuration Parameter "Offset" of a RTD
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Offset".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 7
            persistent: Store parameter permanently if true
            offset: Parameter "Offset" 
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or offset value is out of range
        """
        return super(LucidControlRT8, self).setParamOffset(channel, persistent, offset)
 
    
    def getDeviceTypeName(self):
        """Get device type name as string.
        
        Returns:
            String of the device type name
        
        Raises:
            ValueError: ID data not valid
        """
        return super(LucidControlRT8, self).getDeviceTypeName()
    
    
    def getDeviceType(self):
        """Get device type.
        
        Returns:
            Device type
        """
        return super(LucidControlRT8, self).getDeviceType()


    def __init__(self, portName):
        """
        Constructor of LucidControl RTD Input USB Module class
        """
        LucidControl.__init__(self, portName)
        self.nrOfChannels = 8