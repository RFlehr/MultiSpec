# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:41:30 2016

@author: Flehr
"""

import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

class Plot(QtGui.QWidget):
    def __init__(self, channelList = [1,], parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        
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
        
        self.__plot = self.createPlot()
        self.initSpectra()
        
        lay = QtGui.QVBoxLayout(self)
        lay.addWidget(self.__plot)
        
        
     
    def createPlot(self):
        t = pg.PlotWidget()
        t.setLabel('bottom','Wavelength [nm]')
        t.setLabel('left','Amplitude [dBm]')
        t.setBackground(pg.mkColor(self.backColor))
        return t
        
        
        
    def initSpectra(self):
        self.__sCurves = []
        self.__plot.clear()
        for ch in self.__channelList:
            spec = pg.PlotCurveItem(pen=QtGui.QPen(self.colArray[ch-1],self.lineWidth))
            self.__plot.addItem(spec)
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
            self.__plot.setLabel('left','Amplitude [dBm]')
        else:
            self.__plot.setLabel('left','Amplitude')
        
        
        