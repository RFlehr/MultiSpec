# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 18:12:30 2016

@author: Roman
"""

import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui

class TracePlot(QtGui.QWidget):
    def __init__(self, channelList = [1,], parent=None):
        QtGui.QWidget.__init__(self, parent=None)
        
        self.__traces = []
        self.__channelList = channelList
        #colors
        blue  = QtGui.QColor(0,0,255)
        red = QtGui.QColor(255,0,0)
        green  = QtGui.QColor(0,255,0)
        black = QtGui.QColor(0,0,0)
        
        self.colArray = [blue, red, green, black]
        
        self.lineWidth = 0
        self.backColor = QtGui.QColor(255,255,255)
        self.__plot = self.createPlot()
        #self.initTraces()
        
        lay = QtGui.QVBoxLayout(self)
        lay.addWidget(self.__plot)
        lay.addWidget(self.createPlotOptions())
        
        self.updateViews()
        self.__plot.getViewBox().sigResized.connect(self.updateViews)
        
        
     
    def createPlot(self):
        t = pg.PlotWidget()
        t.setLabel('bottom','Zeit [s]')
        t.setLabel('left','Wellenlänge [nm]')
        t.setBackground(pg.mkColor(self.backColor))
        self.aR = pg.ViewBox()
        t.showAxis('right')
        t.scene().addItem(self.aR)
        t.getAxis('right').linkToView(self.aR)
        self.aR.setXLink(t)
        t.getAxis('right').setLabel(u'Temperatur [\u00b0C]')
        return t
     
    def createPlotOptions(self):
        l = QtGui.QLabel(text='Temperatur')
        self.showTempPlot = QtGui.QCheckBox()
        self.showTempPlot.setChecked(True)
        self.showTempPlot.stateChanged.connect(self.showTemp)
        w = QtGui.QWidget()
        lay = QtGui.QHBoxLayout()
        lay.addStretch()
        lay.addWidget(l)
        lay.addWidget(self.showTempPlot)
        lay.addStretch()
        w.setLayout(lay)
        
        return w
        
    def initTraces(self, numPeaks, sumPeaks):
        print('Init Traces')
        self.__traces = []
        self.__plot.clear()
        numTraces = sumPeaks
        n=0
        for i, numP in enumerate(numPeaks):
            for j in range(numP):
                pt = pg.PlotCurveItem(pen=(n, numTraces))
                self.__plot.addItem(pt)
                self.__traces.append(pt)
                n+=1
        self.__tempTrace = pg.PlotCurveItem(pen=QtGui.QPen(self.colArray[3],0))
        self.aR.addItem(self.__tempTrace)
        
    def setChannelList(self, chList):
        self.__channelList = chList
        
        
    def showTemp(self, state):
        if state:
            pass
        else:
            pass
        
    def plotTemp(self,tempArray):
        t = tempArray
        self.__tempTrace.setData(t[0],t[1]) 
        
        
    def plotTraces(self, numChannels, numPeaks, _fbg):
        numTraces = len(self.__traces)
        sumPeaks = sum(numPeaks)
        if numTraces != sumPeaks:
            self.initTraces(numPeaks, sumPeaks)
        n=0
        for i, numP in enumerate(numPeaks):
            #print(numP)
            for j in range(numP):
             #   
                x,y = _fbg.channels[numChannels[i]-1].getTrace(j)
                self.__traces[n].setData(x,y)
                n+=1
        
    def updateViews(self):
        self.aR.setGeometry(self.__plot.getViewBox().sceneBoundingRect())
        self.aR.linkedViewChanged(self.__plot.getViewBox(), self.aR.XAxis)