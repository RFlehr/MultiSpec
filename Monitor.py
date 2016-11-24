# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:57:48 2016

@author: Flehr
"""

import Queue, threading, time
import numpy as np
from tc08usb import TC08USB, USBTC08_TC_TYPE, USBTC08_ERROR#, USBTC08_UNITS



class MonitorHyperionThread(threading.Thread):
    def __init__(self, dataQ, device, chList, specDevider=1):
        threading.Thread.__init__(self)
        
        self.dataQ = dataQ
        self.alive = threading.Event()
        self.alive.set()
        self.streamDev = specDevider
        
        self.h1 = device
        self.channelList = chList
        
        
    def run(self):
        self.h1.enable_spectrum_streaming(streamingDivider = self.streamDev)
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
        


class MonitorTC08USBThread(threading.Thread):
    def __init__(self, device, dataQ):
        threading.Thread.__init__(self)
        
        self.dataQ = dataQ
        self.alive = threading.Event()
        self.alive.set()    
        self.tc08 = device
        self.tc08.set_mains(50)
        self.tc08.set_channel(0, USBTC08_TC_TYPE.C)
        self.tc08.set_channel(1, USBTC08_TC_TYPE.K)
        self.tc08.set_channel(2, USBTC08_TC_TYPE.K)
        
    def join(self, timeout = None):
        self.alive.clear()
        threading.Thread.join(self, timeout) 
        
    def run(self):
        while self.alive.isSet():
            self.tc08.get_single()
            temp = self.tc08[1]
            temp2 = self.tc08[2]
            #print(temp, temp2)
            self.dataQ.put((temp, temp2))
            
        
        