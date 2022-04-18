'''
Created on 11.06.2013

@author: Klaus Ummenhofer
'''

class IoReturn(object):
    IO_RETURN_OK                = 0
    IO_RETURN_NSUP              = 0xA0
    IO_RETURN_INV_LENGTH        = 0xB0
    IO_RETURN_INV_P1            = 0xB2
    IO_RETURN_INV_P2            = 0xB4
    IO_RETURN_INV_VALUE         = 0xB6
    IO_RETURN_INV_IOCH          = 0xB8
    IO_RETURN_INV_PARAM         = 0xBA
    IO_RETURN_INV_DATA          = 0xC0
    IO_RETURN_ERR_EXEC          = 0xD0
    IO_RETURN_ERR_INTERNAL      = 0xFF