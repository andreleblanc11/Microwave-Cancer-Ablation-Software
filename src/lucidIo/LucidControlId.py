'''
Created on 14.06.2013

@author: Klaus Ummenhofer
'''
class LucidControlId(object):
    def __init__(self):
        self.validData = False
        self.revisionFw =  0
        self.revisionHw = 0
        self.deviceClass = 0
        self.deviceType = 0
        self.deviceSnr = 0

    def init(self, revisionFw, revisionHw, deviceClass, deviceType, deviceSnr):
        self.revisionFw = revisionFw
        self.revisionHw = revisionHw
        self.deviceClass = deviceClass
        self.deviceType = deviceType
        self.deviceSnr = deviceSnr


    def invalid(self):
        self.validData = False