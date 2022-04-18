'''
Created on 13.06.2013
LucidControl Digital Input USB Module DI4 implementation
@author: Klaus Ummenhofer
'''
from lucidIo.LucidControl import LucidControl
from lucidIo.LucidControlDI import LucidControlDI


class LucidControlDI4(LucidControlDI):
    """LucidControl Digital Input USB Module DI4 class
    """

    def getIo(self, channel, value):
        """Get the value or state of one digital input channel.
            
        This method calls the GetIo function of the module and returns
        the value or of the digital input channel.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            value: Digital value object of type ValueDI1 or ValueCNT2.
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getIo(channel, value)


    def getIoGroup(self, channels, values):
        """Get the values of a group of digital input channels.
            
        This method calls the GetIoGroup function of the module and
            returns the values of a group of input channels.
        
        Args:
            channels: Tuple with 4 boolean values (one for each channel).
                A channel is only read if the corresponding channel is
                true.
            values: Digital values.
                A tuple with 4 digital value objects of type ValueDI1 or
                ValueCNT2. The function fills the objects with read data.
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getIoGroup(channels, values)


    def getParamValue(self, channel, value):
        """Get the Configuration Parameter "Value" of a digital
            input channel.
            
        This method calls the GetParam function of the module and returns
            the value of the Configuration Parameter "Value".
        
            The Configuration Parameter "Value" contains the current
            value of the input channel.
        
        It is recommended to call getIo instead of this method.
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            value: Digital value object of type ValueDI1.
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamValue(channel, value)


    def getParamMode(self, channel, mode):
        """Get the Configuration Parameter "Mode" of the digital input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Mode".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            mode: Operation Mode as a list with one LCDIMode integer value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamMode(channel, mode)


    def setParamModeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Mode" of a digital
            input channel to the default value.
            
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
        return super(LucidControlDI4, self).setParamModeDefault(channel, persistent)


    def setParamMode(self, channel, persistent, mode):
        """Set the Configuration Parameter "Mode" of a digital
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Mode".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            mode: Operation Mode as LCDIMode integer value
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range    
        """
        return super(LucidControlDI4, self).setParamMode(channel, persistent, mode)


    def setParamFlagsDefault(self, channel, persistent):
        """Set the Configuration Parameter "Flags" of a digital
            input to the default value.
            
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
        return super(LucidControlDI4, self).setParamFlagsDefault(channel, persistent)


    def getParamFlagAddCounter(self, channel, addCounter):
        """Get the Configuration Parameter Flag "Add Counter".
        
        This method calls the GetParam function of the module and
        returns the Configuration Flag "Add Counter".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            addCounter: Parameter Flag "Add Counter" as a list containing
                one boolean value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamFlagAddCounter(channel, addCounter)


    def setParamFlagAddCounter(self, channel, persistent, addCounter):
        """Set the Configuration Parameter Flag "Add Counter".
        
        This method calls the SetParam function of the module and
        sets the Configuration Flag "Add Counter".
        
         Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            addCounter: Parameter Flag "Add Counter" as boolean
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).setParamFlagAddCounter(channel, persistent, addCounter)

    
    def getParamFlagResetCounterRead(self, channel, resetCounterRead):
        """Get the Configuration Parameter Flag "Reset Counter on Read".
        
        This method calls the GetParam function of the module and
        returns the Configuration Flag "Reset Counter on Read".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            resetCounterRead: Parameter Flag "Reset Counter on Read"
                as a list containing one boolean value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamFlagResetCounterRead(channel, resetCounterRead)


    def setParamFlagResetCounterRead(self, channel, persistent,
        resetCounterRead):
        """Set the Configuration Parameter Flag "Reset Counter on Read".
        
        This method calls the SetParam function of the module and
        sets the Configuration Flag "Reset Counter on Read".
        
         Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            resetCounterRead: Parameter Flag 
                "Reset Counter on Read" as boolean
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).setParamFlagResetCounterRead(channel, persistent, resetCounterRead)


    def getParamFlagInverted(self, channel, inverted):
        """Get the Configuration Parameter Flag "Inverted".
        
        This method calls the GetParam function of the module and
        returns the Configuration Flag "Inverted".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            inverted: Parameter Flag "Inverted" as a list containing
                one boolean value
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamFlagInverted(channel, inverted)
 
    
    def setParamFlagInverted(self, channel, persistent, inverted):
        """Set the Configuration Parameter Flag "Inverted".
        
        This method calls the SetParam function of the module and
        sets the Configuration Flag "Inverted".
        
         Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            inverted: Parameter Flag "Inverted" as boolean
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).setParamFlagInverted(channel, persistent, inverted)


    def getParamScanTime(self, channel, scanTime):
        """Get the Configuration Parameter "Scan Time" of the digital input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Scan Time".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            scanTime: Parameter "Scan Time" as a list containing one integer
                value in microseconds
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamScanTime(channel, scanTime)
        
    
    def setParamScanTimeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Scan Time" of a digital
            input to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Scan Time" to the default value.
        
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
        return super(LucidControlDI4, self).setParamScanTimeDefault(channel, persistent)
    
    
    def setParamScanTime(self, channel, persistent, scanTime):
        """Set the Configuration Parameter "Scan Time" of a digital
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Scan Time".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            scanTime: Parameter "Scan Time" in microseconds
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or cycleTime value is out of range
        """
        return super(LucidControlDI4, self).setParamScanTime(channel, persistent, scanTime)


    def getParamCountTime(self, channel, countTime):
        """Get the Configuration Parameter "Count Time" of the digital input
            channel.
            
        This method calls the GetParam function of the module and returns
            the Configuration Parameter "Count Time".
          
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            countTime: Parameter "Count Time" as a list containing one
                integer value in microseconds
            
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel value is out of range
        """
        return super(LucidControlDI4, self).getParamCountTime(channel, countTime)        
        
    
    def setParamCountTimeDefault(self, channel, persistent):
        """Set the Configuration Parameter "Count Time" of a digital
            input to the default value.
            
        This method calls the SetParam function of the module and sets
        the Configuration Parameter "Count Time" to the default value.
        
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
        return super(LucidControlDI4, self).setParamCountTimeDefault(channel, persistent)
    
    
    def setParamCountTime(self, channel, persistent, countTime):
        """Set the Configuration Parameter "Count Time" of a digital
            input channel.
            
        This method calls the SetParam function of the module and sets the
        Configuration Parameter "Count Time".
        
        Args:
            channel: IO channel number. Must be in the range 0 ... 3
            persistent: Store parameter permanently if true
            countTime: Parameter "Count Time" in microseconds
        
        Returns:
            IO_RETURN_OK in case of success, otherwise detailed IoReturn
            error code.
        
        Raises:
            TypeError: Passed argument types are wrong
            ValueError: Channel or cycleTime value is out of range
        """
        return super(LucidControlDI4, self).setParamCountTime(channel, persistent, countTime)
    
   
    def getDeviceTypeName(self):
        """Get device type name as string.
        
        Returns:
            String of the device type name
        
        Raises:
            ValueError: ID data not valid
        """
        return super(LucidControlDI4, self).getDeviceTypeName()

            
    def getDeviceType(self):
        """Get device type.
        
        Returns:
            Device type
        """
        return super(LucidControlDI4, self).getDeviceType()

                
    def __init__(self, portName):
        """
        Constructor of LucidControl Digital Input USB Module class
        """
        LucidControl.__init__(self, portName)
        self.nrOfChannels = 4
        
        