# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:57:48 2016

@author: Flehr
"""

import Queue, threading, time
import numpy as np



class MonitorThread(threading.Thread):
    def __init__(self, dataQ, device, chList):
        threading.Thread.__init__(self)
        
        self.dataQ = dataQ
        self.alive = threading.Event()
        self.alive.set()
        
        self.h1 = device
        self.channelList = chList
        
        
    def run(self):
        self.h1.enable_spectrum_streaming()
        while self.alive.isSet():
            self.h1.stream_raw_spectrum()
            
            if len(self.channelList) == 0:
                    channelList = np.arange(4)
            else:
                    channelList = np.array(self.channelList) - 1
                    
            data = np.reshape(self.h1.spectrum.data, 
                    (self.h1.spectrum.numChannels, self.h1.spectrum.numPoints))[channelList,:]
            
            spectrumOffsets = np.array(self.h1.offset)[channelList]
            spectrumInvScales = np.array(self.h1.invScale)[channelList]
            data = data.T*spectrumInvScales + spectrumOffsets
            data = data.T
            if len(data) > 0:
                self.dataQ.put((data, time.time()))
        
       
        
    def join(self, timeout = None):
        self.alive.clear()
        threading.Thread.join(self, timeout)   
        
    def setChannelList(self, chList):
        self.channelList = chList
        
    