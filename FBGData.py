# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 12:32:40 2016
ToDo:
    - 

@author: Flehr
"""
import numpy as np
from scipy.ndimage.interpolation import shift
from lmfit.models import GaussianModel, LorentzianModel, LinearModel, VoigtModel, PseudoVoigtModel
import time


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
                
    def getTimeTrace(self):
        return self.traces[0,:self.__numTracePoints]
        
    def getTrace(self, numTrace):
        y = self.traces[numTrace+1,:self.__numTracePoints]
        return y
        
    def getLastValues(self, numPeaks):
        val = []
        for i in range(numPeaks):
            val.append(self.traces[i+1,self.__numTracePoints])
        return val
        
        
class FBGData():
    def __init__(self):
        self.__numChannels = 4
        self.channels = []
        
        self.deltaDBm = 10  #delta dBm to recognize peak
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
        
    def peakFit(self, x, y, model = 'gau', pi = None):
        ti = time.time()
        if pi:
            NumPeaks = len(pi)
            center = []
            fitFuncs = {'gau':GaussianModel, 
                        'lor':LorentzianModel,
                        'voi':VoigtModel, 
                        'psv':PseudoVoigtModel}
            
            paramStr = ['center','sigma','amplitude']
            
            _y = np.power(10,y/10) #np.array(y)- np.min(y)
            
            if NumPeaks > 0:
                peakFuncs = []
                
            for i in range(NumPeaks):
                prefix_str = 'P' + str(i+1) + '_'
                #print('i: ',i)
                peakFuncs.append(fitFuncs[model](prefix=prefix_str))
                if i == 0:            
                    pars = peakFuncs[i].make_params()
                else:
                    pars.update(peakFuncs[i].make_params())
                    
                pars[str(prefix_str + paramStr[0])].set(x[pi[i]])#, min=peak_wl[i]-1.0, max=peak_wl[i]+1.0)
                pars[str(prefix_str + paramStr[1])].set(.1, max=1.0)
                pars[str(prefix_str + paramStr[2])].set(_y[pi[i]], min=0)
                
                if i == 0:            
                    mod = peakFuncs[i]
                else:
                   mod += peakFuncs[i] 
                       
            lin_mod = LinearModel()
            pars.update(lin_mod.make_params())
            pars['slope'].set(0.0)
            pars['intercept'].set(0.0)
            
            #mod += lin_mod
            out = mod.fit(_y, pars, x=x)
            #self.Spec[index].yfit = out.best_fit
            self.facFWHM = {'gau':2.3548, 'lor': 2.0, 'voi':3.6013,'psv':2.1774}
                        
            for i in range(NumPeaks):
                prefix_str = 'P' + str(i+1) + '_'
                center.append(out.best_values[str(prefix_str + paramStr[0])])
                #print('Center: ', out.best_values[str(prefix_str + paramStr[0])])
            #print(index,self.Spec[index].name)        
            #print(out.fit_report(min_correl=0.5))
            print 'fit :', time.time()-ti
            return center
    
    def searchPeaks(self, x, y, channelList, cs = None, timestamp = 0, peakfit = 0):
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
                    if not peakfit:
                        peaks = self.centerOfGravity(x,y[i],pi, deltaI)
                    else:
                        peaks = self.peakFit(x, y[i], pi= pi)
                        
                    self.channels[channelList[i]-1].setPeaks(timestamp, peaks)
                
                #print(peakWl)
            if cs:
                cs.setNumPeaksCh(channelList[i], numPeaks[i])

        return numPeaks
        