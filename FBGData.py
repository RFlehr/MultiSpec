# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 12:32:40 2016
ToDo:
    - 

@author: Flehr
"""
import numpy as np
from time import time

from scipy.ndimage.interpolation import shift


class PeakData():
    def __init__(self, center):
        self.__center = center
        self.__fwhw = 0.0
        self.__amplitude = 0.0
        
    def Center(self):
        return self.__center

    def FWHM(self):
        if self.__fwhw:
            return self.__fwhw

    def Amp(self):
        if self.__amplitude:
            return self.__amplitude    
        
    def setAmp(self, amp):
        self.__amplitude = amp
        
    def setFWHM(self, fwhm):
        self.__fwhw = fwhm

    def setTime(self, time):
        self.__timestamp = time
        
class Channel():
    def __init__(self):
        
        self.__maxPeaks = 30
        self.__maxBuffer = 5000
        self.__numTracePoints = 0
        self.traces = np.zeros((self.__maxPeaks+1,self.__maxBuffer))#col[0] timestamp        

        
    def setPeaks(self, timest, peakArray):
        self.__numTracePoints = np.count_nonzero(self.traces[0])
        for i, val in enumerate(peakArray):
            if self.__numTracePoints < self.__maxBuffer:
                self.traces[i+1][self.__numTracePoints] = val
                self.traces[0][self.__numTracePoints] = timest
            else:
                self.traces[i+1] = shift(self.traces[i+1], -1, cval = val)
                self.traces[0] = shift(self.traces[0], -1, cval = timest)
        #print(self.__numTracePoints)
        
    def getTrace(self, numTrace):
        x = self.traces[0,:self.__numTracePoints-1]
        y = self.traces[numTrace+1,:self.__numTracePoints-1]
        return x, y
        
    def getLastValues(self, numPeaks):
        val = []
        for i in range(numPeaks):
            val.append(self.traces[i+1,-1])
        return val
        
        
class FBGData():
    def __init__(self):
        self.__numChannels = 4
        self.channels = []
        
        self.deltaDBm = 10  #deta dBm to recognize peak
        self.threshold = 5 
        self.peakWindow = 2
        
        for i in range(self.__numChannels):
            self.channels.append(Channel())
        
    def centerOfGravity(self, x, y, pi, di):
        numVal = len(x)
        _y = np.array(y)- np.min(y)
        cog = []
        for i in range(len(pi)):
            pImin = pi[i]-di
            if pImin < 0:
                pImin = 0
            pImax = pi[i] + di
            if pImax > (numVal-1):
                pImax = numVal-1
            cy = _y[pImin:pImax]
            cx = x[pImin:pImax]
            cog.append((cx*cy).sum()/cy.sum())
        return cog
    
    def searchPeaks(self, x, y, channelList, cs = None, timestamp = 0):
        st = time()
                    
        x=np.array(x)
        numSpecs = len(channelList)
        numPeaks = []
        dX = x[1]-x[0]
        numVal = len(x)
        deltaI = int(self.peakWindow/dX)
        for i in range(numSpecs): 
            try:
                _y = np.array(y[i])
            except Exception as e:
                print(e)
            ymin = np.min(_y)
            ymax = np.max(_y)
            if ymax - ymin < self.deltaDBm:
                numPeaks.append(0)
            else:
                thres = ymax-self.threshold
                peakIndex = []; peakVal = []
                aboveThres = True
                n = 0
                while aboveThres and n<30:
                    n += 1
                    ymax = np.max(_y)
                    if ymax > thres:
                        peakVal.append(float(ymax))
                        pI = np.argmax(_y)
                        peakIndex.append(pI)
                        pImin = pI-deltaI
                        if pImin < 0:
                            pImin = 0
                        pImax = pI + deltaI
                        if pImax > (numVal-1):
                            pImax = numVal-1
                        _y[pImin:pImax] = ymin
                        aboveThres = True
                    else:
                        aboveThres = False
                numPeaks.append(len(peakIndex))
                
                if numPeaks[i]:
                    pi = sorted(peakIndex)
                    cog = self.centerOfGravity(x,y[i],pi, deltaI)
                    self.channels[channelList[i]-1].setPeaks(timestamp, cog)
                
                #print(peakWl)
            if cs:
                cs.setNumPeaksCh(channelList[i], numPeaks[i])

        #print(time()-st) 
        return numPeaks
        