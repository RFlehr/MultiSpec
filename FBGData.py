# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 12:32:40 2016

@author: Flehr
"""
import numpy as np

class PeakData():
    def __init__(self, center):
        self.__center = center
        self.__fwhw = 0.0
        self.__amplitude = 0.0
        self.__timestamp = 0.0
        
    def getCenter(self):
        return self.__center

    def getFWHM(self):
        return self.__fwhw

    def getAmp(self):
        return self.__amplitude    
        
    def getTime(self):
        return self.__timestamp
        
    def setAmp(self, amp):
        self.__amplitude = amp
        
    def setFWHM(self, fwhm):
        self.__fwhw = fwhm

    def setTime(self, time):
        self.__timestamp = time
        
class Channel():
    def __init__(self):
        
        self.__numPeaks = 0
        self.__traces = []

    def getNumPeaks(self):
        return self.__numPeaks        
        
    def setNumPeaks(self, num):
        self.__numPeaks = num
        
class FBGData():
    def __init__(self):
        self.__numChannels = 4
        self.__channels = []
        
        for i in range(self.__channels):
            self.__channels.append(Channel())
        
    
    
    def searchPeaks(self, x, y, channelList):
        numSpecs = len(channelList)
        for i in range(numSpecs): 
            _y = y[i]
            #check for peak
            
            pass
        