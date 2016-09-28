# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 12:32:40 2016
ToDo:
    - 

@author: Flehr
"""
import numpy as np
from scipy.ndimage.interpolation import shift
from lmfit.models import GaussianModel
import time
from scipy.optimize import curve_fit

class Channel():
    def __init__(self):
        
        self.__maxPeaks = 30
        self.__maxBuffer = 5000
        self.__numTracePoints = 0
        self.traces = np.zeros((self.__maxPeaks,self.__maxBuffer), dtype={'names':['time', 'cen', 'max', 'cenmax', 'cog', 'fwhm', 'amp'], 'formats':['f4','f4','f4','f4','f4','f4','f4']})#col[0] timestamp 
        self.num = -1

        
    def setPeaks(self, timest, peakArray, maxArray, cenMax, cog = None, fwhmArray = None, ampArray = None):
        self.__numTracePoints = np.count_nonzero(self.traces[0])
        for i, val in enumerate(peakArray):
            if self.__numTracePoints < self.__maxBuffer:
                self.traces[i][self.__numTracePoints]['cen'] = val
                self.traces[i][self.__numTracePoints]['max'] = maxArray[i]
                self.traces[i][self.__numTracePoints]['cenmax'] = cenMax[i]
                self.traces[i][self.__numTracePoints]['time'] = timest
                if cog:
                    self.traces[i][self.__numTracePoints]['cog'] = cog[i]
                if fwhmArray:
                    self.traces[i][self.__numTracePoints]['fwhm'] = fwhmArray[i]
                if ampArray:
                    self.traces[i][self.__numTracePoints]['amp'] = ampArray[i]
            else:
                self.traces[i] = np.roll(self.traces[i], -1)
                self.traces[i][-1]['cen'] = val
                self.traces[i][-1]['max'] = maxArray[i]
                self.traces[i][-1]['cenmax'] = cenMax[i]
                self.traces[i][-1]['time'] = timest
                if cog:
                    self.traces[i][-1]['cog'] = cog[i]
                if fwhmArray:
                    self.traces[i][-1]['fwhm'] = fwhmArray[i]
                if ampArray:
                    self.traces[i][-1]['amp'] = ampArray[i]
  
    def getTimeTrace(self):
        return self.traces[0,:self.__numTracePoints]['time']
        
    def getTraceMax(self, numTrace):
        y = self.traces[numTrace,:self.__numTracePoints]['max']
        return y
        
    def getTraceFWHM(self, numTrace):
        y = self.traces[numTrace,:self.__numTracePoints]['fwhm']
        return y
        
    def getTrace(self, numTrace):
        y = self.traces[numTrace,:self.__numTracePoints]['cen']
        return y
        
    def getLastValues(self, numPeaks):
        val = []; fwhm = []; amp = []; _max = []; cmax = []; cog = []
        t = 0.; f = 0.; a = 0.; c=0
        if self.__numTracePoints:
            point = self.__numTracePoints-1
            for i in range(numPeaks):
                #print(self.traces[i,self.__numTracePoints])
                val.append(self.traces[i,point]['cen'])
                _max.append(self.traces[i,point]['max'])
                cmax.append(self.traces[i,point]['cenmax'])
                t = self.traces[i][point]['time']
                c = self.traces[i][point]['cog']
                if c: cog.append(c)
                f = self.traces[i][point]['fwhm']
                if f: fwhm.append(f)
                a = self.traces[i][point]['amp']
                if a: amp.append(a)
       
        #print(t,val,fwhm,amp)
        return t, val, _max, cmax, cog, fwhm, amp
        

        
        
class FBGData():
    def __init__(self):
        self.__numChannels = 4
        self.channels = []
        
        self.deltaDBm = 5  #delta dBm to recognize peak
        self.threshold = -14. 
        self.peakWindow = 7
        
        self.thresArray = [-28.5, -28.5, -28.5 -28.5]
        
        for i in range(self.__numChannels):
            self.channels.append(Channel())
        
    def centerOfGravity(self, x, y, pi, di):
        numVal = len(x)
        _y = np.array(y)- np.min(y)
        _y = np.power(10,_y/10)
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
            up = 0.
            do = 0.
            for i in range(len(cy)):
                up += cx[i]*cy[i]
                do += cy[i]
            cog.append(up/do)
            #cog.append((cx*cy).sum()/cy.sum())
        return cog
        
    def peakFit(self, x, y, model = 'gau', pi = None, di = None):
        ti = time.time()
        if pi:
            NumPeaks = len(pi)
            center = []
            fwhm = []
            amp = []
            numVal = len(x)
            for i in range(NumPeaks):
                pImin = pi[i]-di
                if pImin < 0:
                    pImin = 0
                pImax = pi[i] + di
                if pImax > (numVal-1):
                    pImax = numVal-1
                __y = y[pImin:pImax]
                __x = x[pImin:pImax]
                
                __y = np.power(10,__y/10) #np.array(y)- np.min(y)
                
                mod = GaussianModel()
                pars = mod.guess(__y, x=__x)
                out  = mod.fit(__y, pars, x=__x)
                center.append(out.best_values['center'])
                fwhm.append(out.best_values['sigma']*2.3548)
                amp.append(out.best_values['amplitude'])
            #print 'fit:', time.time()-ti
            return center, fwhm ,amp
    
    def searchPeaks(self, x, y, channelList, cs = None, timestamp = 0, peakfit = 0):
        x=np.array(x)
        numSpecs = len(channelList)
        numPeaks = []
        dX = x[1]-x[0]
        numVal = len(x)
        deltaI = int(self.peakWindow/dX)
        deltaCog = int(1/dX)
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
                thres = ymin - self.threshold#self.thresArray[i]#
                peakIndex = []; peakVal = []; peakValWl =[]
                aboveThres = True
                n = 0
                while aboveThres and n<30:
                    n += 1
                    ymax = np.max(_y)
                    #print(ymax, thres)
                    if ymax > thres:
                        peakVal.append(float(ymax))
                        pI = np.argmax(_y)
                        peakValWl.append(x[pI])
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
                    pi, peakVal, peakValWl = zip(*sorted(zip(peakIndex, peakVal,peakValWl)))
                    if not peakfit:
                        peaks = self.centerOfGravity(x,y[i],pi, deltaCog)
                        self.channels[channelList[i]-1].setPeaks(timestamp, peaks, peakVal, peakValWl)
                    else:
                        peaks, fwhm, amp = self.peakFit(x, y[i], pi= pi, di=deltaI)
                        cog = self.centerOfGravity(x,y[i],pi, deltaI)
                        self.channels[channelList[i]-1].setPeaks(timestamp, peaks, peakVal, peakValWl, cog, fwhm, amp)
                        
            if cs:
                cs.setNumPeaksCh(channelList[i], numPeaks[i])

        return numPeaks
        
    def gauss(self,x, center, amp, sig, off):
        up = x - center
        up2 = up*up
        down = 2*sig*sig
        frac = up2/down * -1
        _exp = np.exp(frac)
        
        return amp*_exp + off
        
    def peakFit_(self, x, y):
        p0 = [x[np.argmax(y)], 30, .2, -60]
        #y = np.power(10,y/10)
        popt, pcov = curve_fit(self.gauss, x, y, p0)
        #self.plotW.plotS(x,self.gauss(x, popt[0],popt[1],popt[2],popt[3]))
        #print(popt)
        return popt