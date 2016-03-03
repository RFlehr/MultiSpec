# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:41:30 2016

@author: Flehr
"""

import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

class Plot(pg.PlotWidget):
    def __init__(self, channelList = [1,], parent=None):
        pg.PlotWidget.__init__(self, parent)
        
        
        self.__Spectrum = None
        self.__sCurves = []
        self.__channelList = channelList
        self.__numSpecs = len(self.__channelList)
        self.__dBm = True
        self.lineWidth = 0
        self.backColor = QtGui.QColor(255,255,255)
        
        #colors
        blue  = QtGui.QColor(0,0,255)
        red = QtGui.QColor(255,0,0)
        green  = QtGui.QColor(0,255,0)
        black = QtGui.QColor(0,0,0)
        
        self.colArray = [blue, red, green, black]
        
        self.createPlot()
        self.initSpectra()
        
        
     
    def createPlot(self):
        self.setLabel('bottom','Wavelength [nm]')
        self.setLabel('left','Amplitude [dBm]')
        self.setBackground(pg.mkColor(self.backColor))
        
        
        
    def initSpectra(self):
        self.__sCurves = []
        self.clear()
        for ch in self.__channelList:
            spec = pg.PlotCurveItem(pen=QtGui.QPen(self.colArray[ch-1],self.lineWidth))
            self.addItem(spec)
            self.__sCurves.append(spec)
        
    def plotS(self, x, y):
        _x = x
        if not self.__dBm:
            y = np.power(10,y/10)
        for i in range(self.__numSpecs):
            try: 
                self.__sCurves[i].setData(_x, y[i])
            except:
              pass  
        
    def setChannelList(self, chList):
        self.__channelList = chList
        self.__numSpecs = len(chList)
        self.initSpectra()
        
    def setdBm(self, isdBm):
        self.__dBm = isdBm
        if isdBm:
            self.setLabel('left','Amplitude [dBm]')
        else:
            self.setLabel('left','Amplitude')
        
        
        