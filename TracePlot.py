# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 18:12:30 2016

ToDo:
    - add Legend

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
        self.YAxisLabel = ['Wellenlänge [nm]', 'Amplitude [dBm]' , 'FWHM [nm]', u'\u0394Wellenlänge [pm]']
        
        self.lineWidth = 0
        self.backColor = QtGui.QColor(255,255,255)
        plotOptions = self.createPlotOptions()
        self.__plot = self.createPlot()
        #self.initTraces()
        
        lay = QtGui.QVBoxLayout(self)
        lay.addWidget(self.__plot)
        lay.addWidget(plotOptions)
        
        self.updateViews()
        self.__plot.getViewBox().sigResized.connect(self.updateViews)
    
    def changePlot(self):
        self.__plot.setLabel('left',self.YAxisLabel[self.selectPlotData.currentIndex()])     
        
    def changePlotData(self, data):
        self.changePlot()      
        
    def clearPlot(self):
        self.__plot.clear()
        self.aR.clear()
     
    def createPlot(self):
        t = pg.PlotWidget()
        t.setLabel('bottom','Zeit [s]')
        t.setLabel('left',self.YAxisLabel[self.selectPlotData.currentIndex()])
        t.setBackground(pg.mkColor(self.backColor))
        self.aR = pg.ViewBox()
        t.showAxis('right')
        t.scene().addItem(self.aR)
        t.getAxis('right').linkToView(self.aR)
        self.aR.setXLink(t)
        t.getAxis('right').setLabel(u'Temperatur [\u00b0C]')
        self.legend = t.addLegend()
        return t
     
    def createPlotOptions(self):
        l = QtGui.QLabel(text='Temperatur')
        self.showTempPlot = QtGui.QCheckBox()
        self.showTempPlot.setChecked(True)
        self.showTempPlot.stateChanged.connect(self.showTemp)
        self.selectPlotData = QtGui.QComboBox(self)
        self.selectPlotData.addItems(['Center','Amplitude','FWHM', u'\u0394Center'])
        self.selectPlotData.currentIndexChanged.connect(self.changePlotData)
        
        w = QtGui.QWidget()
        lay = QtGui.QHBoxLayout()
        lay.addStretch()
        lay.addWidget(l)
        lay.addWidget(self.showTempPlot)
        lay.addWidget(QtGui.QLabel(text='PlotData: '))
        lay.addWidget(self.selectPlotData)
        lay.addStretch()
        w.setLayout(lay)
        
        return w
        
    def initTraces(self, numPeaks, sumPeaks):
        print('Init Traces')
        self.__traces = []
        self.__plot.clear()
        self.aR.clear()
        self.__plot.plotItem.legend.items = []
        numTraces = sumPeaks
        n=0
        for i, numP in enumerate(numPeaks):
            label = 'Ch' + str(self.__channelList[i])
            for j in range(numP):
                lab = label + ' FBG' + str(j+1)
                pt = pg.PlotCurveItem(pen=(n, numTraces))
                self.__plot.addItem(pt)
                self.__traces.append(pt)
                self.legend.addItem(pt, lab)
                n+=1
        self.__tempTrace = pg.PlotCurveItem(pen=QtGui.QPen(self.colArray[3],0))
        self.__tempTrace1 = pg.PlotCurveItem(pen=QtGui.QPen(self.colArray[3],0))
        self.aR.addItem(self.__tempTrace)
        self.aR.addItem(self.__tempTrace1)
        self.legend.addItem(self.__tempTrace, 'Temperatur1')
        self.legend.addItem(self.__tempTrace1, 'Temperatur2')
        
    def setChannelList(self, chList):
        self.__channelList = chList
        
        
    def showTemp(self, state):
        if state:
            pass
        else:
            pass
        
    def plotTemp(self,tempArray):
        t = tempArray
        x, l = self.setTimeLabel(t[0])
        self.__tempTrace.setData(x,t[1]) 
        self.__tempTrace1.setData(x,t[2])
        #print(t[2,-1])
        
        
    def plotTraces(self, numChannels, numPeaks, _fbg):
        numTraces = len(self.__traces)
        sumPeaks = sum(numPeaks)
        plotData = self.selectPlotData.currentIndex()
        if numTraces != sumPeaks:
            self.initTraces(numPeaks, sumPeaks)
        n=0
        for i, numP in enumerate(numPeaks):
            #print(numP)
            x = _fbg.channels[numChannels[i]-1].getTimeTrace()
            if len(x) > 1:
                _x, label = self.setTimeLabel(x)
                label = 'Zeit [' + label + ']'
                self.__plot.setLabel('bottom',label)
                for j in range(numP):
                    if plotData == 1:
                        y = _fbg.channels[numChannels[i]-1].getTraceMax(j)
                    elif plotData == 2:
                        y = _fbg.channels[numChannels[i]-1].getTraceFWHM(j)
                    elif plotData == 3:
                        y = _fbg.channels[numChannels[i]-1].getTrace(j)
                    else:
                        y = _fbg.channels[numChannels[i]-1].getTraceMax(j)
                        y = (y - y[0])*1000
                    self.__traces[n].setData(_x,y)
                    n+=1
            
        
                
    def setTimeLabel(self, timearray):
        #time in sec
        label = 's'
        times = timearray
        lasttime = times[-1]
        if lasttime <= 180:
            label = 's'
        elif lasttime <= 18000:
            label = 'min'
            times = times/60.
        else:
            label = 'h'
            times = times/3600.
        
        return times, label
        
    def updateViews(self):
        self.aR.setGeometry(self.__plot.getViewBox().sceneBoundingRect())
        self.aR.linkedViewChanged(self.__plot.getViewBox(), self.aR.XAxis)