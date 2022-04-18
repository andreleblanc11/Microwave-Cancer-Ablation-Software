'''
Created on 11.06.2013
LucidControl Value Classes
@author: Klaus Ummenhofer
'''

from abc import abstractmethod
import struct

class _ValueType(object):
    
    VALUE_TYPE_NONE             = 0
    VALUE_TYPE_DI1              = 0
    VALUE_TYPE_CNT2             = 0x0A
    VALUE_TYPE_ANU2             = 0x10
    VALUE_TYPE_VOU2             = 0x1A
    VALUE_TYPE_VOU4             = 0x1B
    VALUE_TYPE_VOS2             = 0x1C
    VALUE_TYPE_VOS4             = 0x1D
    VALUE_TYPE_CUS4             = 0x23
    VALUE_TYPE_TMS2             = 0x40
    VALUE_TYPE_TMS4             = 0x41
    VALUE_TYPE_RMU2             = 0x50
    
    
class Value(object):
    def __init__(self):
        self._channel = 0
        self._valueType = _ValueType.VALUE_TYPE_NONE
        self._size = 0
        
        @abstractmethod
        def _setData(self, data):
            pass
        
        @abstractmethod
        def _getData(self, data):
            pass
         
    
class ValueDI1(Value):
    """Digital Input / Output value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_DI1
        self._size = 1
        self._value = False
        
    def getValue(self):
        """Returns value
        """
        return self._value
    
    def setValue(self, value):
        """Set value
        """
        self._value = value
        
    def _setData(self, data):
        if (data[0] == 0):
            self._value = False
        else:
            self._value = True
        
    def _getData(self, data):
        if (self._value == True):
            data += bytearray([0x01])
        else:
            data += bytearray([0x00])



class ValueCNT2(Value):
    """Digital Count value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_CNT2
        self._size = 2
        self._value = 0
        
    def getValue(self):
        """Returns value
        """
        return self._value
    
    def setValue(self, value):
        """Set value
        """
        self._value = value
    
    def _setData(self, data):
        self._value = struct.unpack("<H", data)[0]
        
    def _getData(self, data):
        data += bytearray(struct.pack("<H", self._value)) 
        
        

class ValueANU2(Value):
    """Analog value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_ANU2
        self._size = 2
        self._value = 0  
    
    def getValue(self):
        """Returns value
        """
        return self._value
    
    def setValue(self, value):
        """Set value
        """
        self._value = value 
    
    def _setData(self, data):
        self._value= struct.unpack("<H", data)[0]
        
    def _getData(self, data):
        data += bytearray(struct.pack("<H", self._value))

            
class ValueVOS2(Value):
    """Analog Voltage value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_VOS2
        self._size = 2
        self._value = 0
        self._voltage = 0
        
    def getVoltage(self):
        """Get voltage value
        """
        return self._voltage
    
    def setVoltage(self, voltage):
        """Set voltage value
        """
        self._voltage = voltage
        self._value = (int)(self._calcValue(voltage))
        
    def getValue(self):
        """Get integer value
        """
        return self._value
    
    def setValue(self, value):
        """Set integer value
        """
        self._value = value
        self._voltate = self._calcVoltage(value)

    def _calcVoltage(self, value):
        voltage = value
        voltage /= 1000.0
        return voltage
    
    def _calcValue(self, voltage):
        voltage *= 1000
        return voltage 
        
    def _setData(self, data):
        self._value = struct.unpack("<h", data)[0]
        self._voltage = self._calcValue(self._value)
        
    def _getData(self, data):
        data += bytearray(struct.pack("<h", self._value))
        

class ValueVOS4(Value):
    """Analog Voltage value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_VOS4
        self._size = 4
        self._value = 0
        self._voltage = 0
        
    def getVoltage(self):
        """Get voltage value
        """
        return self._voltage
    
    def setVoltage(self, voltage):
        """Set voltage value
        """
        self._voltage = voltage
        self._value = (int)(self._calcValue(voltage))
        
    def getValue(self):
        """Get integer value
        """
        return self._value
    
    def setValue(self, value):
        """Set integer value
        """
        self._value = value
        self._voltage = self._calcVoltage(value)

    def _calcVoltage(self, value):
        voltage = value
        voltage /= 1000000.0
        return voltage
    
    def _calcValue(self, voltage):
        voltage *= 1000000
        return voltage 
        
    def _setData(self, data):
        self._value = struct.unpack("<i", data)[0]
        self._voltage = self._calcVoltage(self._value)
        
    def _getData(self, data):
        data += bytearray(struct.pack("<i", self._value))
        
        
class ValueCUS4(Value):
    """Analog Current value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_CUS4
        self._size = 4
        self._value = 0
        self._current = 0
        
    def getCurrent(self):
        """Get current value
        """
        return self._current
    
    def setCurrent(self, current):
        """Set current value
        """
        self._current = current
        self._value = (int)(self._calcValue(current))
        
    def getValue(self):
        """Get integer value
        """
        return self._value
    
    def setValue(self, value):
        """Set integer value
        """
        self._value = value
        self._current = self._calcCurrent(value)

    def _calcCurrent(self, value):
        current = value
        current /= 1000000.0
        return current
    
    def _calcValue(self, current):
        current *= 1000000
        return current
        
    def _setData(self, data):
        self._value = struct.unpack("<i", data)[0]
        self._current = self._calcCurrent(self._value)
        
    def _getData(self, data):
        data += bytearray(struct.pack("<i", self._value))    
        
        
class ValueTMS2(Value):
    """Temperature Value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_TMS2
        self._size = 2
        self._value = 0
        self._temperature = 0
        
    def getTemperature(self):
        """Get Temperature value
        """
        return self._temperature
    
    def setTemperature(self, temperature):
        """Set Temperature value
        """
        self._temperature = temperature
        self._value = (int)(self._calcValue(temperature))
        
    def getValue(self):
        """Get integer value
        """
        return self._value
    
    def setValue(self, value):
        """Set integer value
        """
        self._value = value
        self._temperature = self._calcTemperature(value)
        
    def _calcTemperature(self, value):
        temperature = value
        temperature /= 10.0
        return temperature
    
    def _calcValue(self, temperature):
        temperature *= 10
        return temperature
        
    def _setData(self, data):
        self._value = struct.unpack("<h", data)[0]
        self._temperature = self._calcTemperature(self._value)
        
    def _getData(self, data):
        data += bytearray(struct.pack("<h", self._value))
        

class ValueTMS4(Value):
    """Temperature Value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_TMS4
        self._size = 4
        self._value = 0
        self._temperature = 0
        
    def getTemperature(self):
        """Get Temperature value
        """
        return self._temperature
    
    def setTemperature(self, temperature):
        """Set Temperature value
        """
        self._temperature = temperature
        self._value = (int)(self._calcValue(temperature))
        
    def getValue(self):
        """Get integer value
        """
        return self._value
    
    def setValue(self, value):
        """Set integer value
        """
        self._value = value
        self._temperature = self._calcTemperature(value)
    
    def _calcTemperature(self, value):
        temperature = value
        temperature /= 100.0
        return temperature
    
    def _calcValue(self, temperature):
        temperature *= 100
        return temperature
    
    def _setData(self, data):
        self._value = struct.unpack("<i", data)[0]
        self._temperature = self._calcTemperature(self._value)
        
    def _getData(self, data):
        data += bytearray(struct.pack("<i", self._value))
    
    
class ValueRMU2(Value):
    """Resistance Value class
    """
    def __init__(self):
        Value.__init__(self)
        self._valueType = _ValueType.VALUE_TYPE_RMU2
        self._size = 2
        self._value = 0
        self._resistance = 0
        
    def getResistance(self):
        """Get resistance value
        """
        return self._resistance
    
    def setResistance(self, resistance):
        """Set resistance value
        """
        self._resistance = resistance
        self._value = (int)(self._calcValue(resistance))
        
    def getValue(self):
        """Get integer value
        """
        return self._value
    
    def setValue(self, value):
        """Set integer value
        """
        self._value = value
        self._resistance = self._calcResistance(value)
    
    def _calcResistance(self, value):
        resistance = value
        resistance /= 10.0
        return resistance
    
    def _calcValue(self, resistance):
        resistance *= 10
        return resistance
    
    def _setData(self, data):
        self._value = struct.unpack("<H", data)[0]
        self._resistance = self._calcResistance(self._value)
        
    def _getData(self, data):
        data += bytearray(struct.pack("<H", self._value))