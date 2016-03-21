# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:36:45 2016

@author: Flehr
ToDo:
    - port save data to fbgdata
"""

__title__ =  'MultiSpec'
__about__ = """Hyperion si255 Interrogation Software
            including Pico Temprature measurements
            """
__version__ = '0.1.2'
__date__ = '16.03.2016'
__author__ = 'Roman Flehr'
__cp__ = u'\u00a9 2016 Loptek GmbH & Co. KG'

import sys
sys.path.append('../')

from pyqtgraph.Qt import QtGui, QtCore
import plot as pl
import TracePlot as tl
from Monitor import MonitorHyperionThread
import hyperion, Queue, os
from time import time, strftime
from scipy.ndimage.interpolation import shift
import numpy as np
from tc08usb import TC08USB, USBTC08_TC_TYPE, USBTC08_ERROR#, USBTC08_UNITS
from FBGData import FBGData
from MyWidgets import ChannelSelection, FreqSpin

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        
        self.HyperionIP = '10.0.0.55'
        self.si255 = None
        self.__wavelength = None
        self.__scaledWavelength = None
        self.__scalePos = None
        self.isConnected = False
        self.channelList = [1,]
        self.peakList = []
        self.__numPeaksArray = [0,0,0,0]
        self.Monitor = None
        self.__freq = 1 #hyperion Spectrum Divider
        self.__maxTempBuffer = 5000
        self.__tempArray = np.zeros((2,self.__maxTempBuffer))
        self.__fbg = FBGData()
        self.logFileName = ''
        self.logFile = None #log-file handle
        
        self.tempConnected = False
        
        self.measurementActive = False
        self.startMeasurementTime = time()
        
        self.plotSpec = pl.Plot(self.channelList)
        self.plotTrace = tl.TracePlot()
        self.plotTab = QtGui.QTabWidget()
        self.plotTab.addTab(self.plotSpec,'Spectra')
        self.plotTab.addTab(self.plotTrace, 'Trace')
        
        self.setWindowTitle(__title__ + ' ' + __version__)
        self.setCentralWidget(self.plotTab)
        
        self.createMenu()
        self.setActionState()
        
    def about(self):
        QtGui.QMessageBox.about(self,'About '+__title__,
            self.tr("""<font size=8 color=red>
                        <b><center>{0}</center></b></font>
                   <br><font size=5 color=blue>
                        <b>{1}</b></font>
                    <br><br>Author: {2}<br>
                    Version: {3}<br>
                    Date: {4}<br><br>""".format(__title__, __about__, __author__, __version__, __date__)+__cp__))
    
    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            try:
                if self.si255.comm.connected:
                    self.si255.comm.close()
                if self.tempConnected:
                    self.tc08usb.close_unit()
            except:
                pass
            event.accept()
        else:
            event.ignore()
        
    def connectHyperion(self):
        try:
            si255Comm = hyperion.HCommTCPSocket(self.HyperionIP, timeout = 5000)
        except hyperion.HyperionError as e:
            print e , ' \thaha'   
        if si255Comm.connected:
            self.si255 = hyperion.Hyperion(comm = si255Comm)
            self.isConnected=True
            self.__wavelength =np.array(self.si255.wavelengths)
            #get wavelength range to reduce data
            _min = self.minWlSpin.value()
            _max = self.maxWlSpin.value()
            self.__scalePos = np.where((self.__wavelength>=_min) & (self.__wavelength<_max))[0]
            self.__scaledWavelength = self.__wavelength[self.__scalePos]
            
        else:
            self.isConnected=False
            QtGui.QMessageBox.critical(self,'Connection Error',
                                       'Could not connect to Spectrometer. Please try again')
        self.setActionState()
        
    def connectTemp(self):
        dll_path = os.path.join(os.getenv('ProgramFiles'),'Pico Technology', 'SDK', 'lib')
        try:
            self.tc08usb = TC08USB(dll_path = dll_path)
            if self.tc08usb.open_unit():
                self.initTempArray()
                self.tc08usb.set_mains(50)
                self.tc08usb.set_channel(1, USBTC08_TC_TYPE.K)
                self.tempConnected = True
                self.updateTempTimer = QtCore.QTimer()
                self.updateTempTimer.timeout.connect(self.getTemp)
                self.updateTempTimer.start(1000)
            else:
                self.tempConnected = False
                self.connectTempAction.setChecked(False)
                QtGui.QMessageBox.critical(self,'Connection Error',
                                       'Could not connect to TC08-USB. Please try again')
                
        except USBTC08_ERROR as e:
            print(e)
            
    def disconnectTemp(self):
        if self.updateTempTimer.isActive():
            self.updateTempTimer.stop()
        self.tc08usb.close_unit()
        self.tc08usb = None
        self.tempConnected = False
        self.__tempArray = None
            
    def createAction(self, text, slot=None, shortcut=None,
                     icon=None,tip=None,checkable=False,
                     signal='triggered()'):
        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon('../icons/%s.png' % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None and not checkable:
            action.triggered.connect(slot)
        elif slot is not None and checkable:
            action.toggled.connect(slot)
        if checkable:
            action.setCheckable(True)
       
        return action
        
    
        
        
    def createMenu(self):
        self.quitAction = self.createAction('Q&uit',slot=self.close,shortcut='Ctrl+Q',
                                            icon='Button Close',tip='Programm schließen')

        self.connectAction = self.createAction('Verbinden', slot=self.connectHyperion,
                                              tip='Spektrometer verbinden', checkable = True,
                                              icon='Button Add')   
        
        self.connectThermoAction = self.createAction('Thermometer', slot=self.toggleThermo, tip='Thermometer verbinden', icon='Thermo', checkable = True)
        
        self.startAction = self.createAction('St&art', slot=self.startMeasurement, shortcut='Ctrl+M',
                                             tip='Messung starten', icon='Button Play')
        
        self.recordAction = self.createAction('Aufnahme', tip='Aufnahme starten', checkable = True, icon='Button Record Red')
        
        self.stopAction = self.createAction('St&op', slot=self.stopMeasurement, shortcut='Ctrl+T',
                                        tip='Messung beenden', icon='Button Stop')
        
        self.channelSelection = ChannelSelection()
        self.channelSelection.setNumPeaks(self.__numPeaksArray)
        self.channelSelection.selectionChanged.connect(self.setChannels)
        self.selectChannelAction = QtGui.QWidgetAction(self)
        self.selectChannelAction.setDefaultWidget(self.channelSelection)
        self.freqSpin = FreqSpin()
        self.freqSpin.valueChanged.connect(self.test)
        self.freqSpinAction = QtGui.QWidgetAction(self)
        self.freqSpinAction.setDefaultWidget(self.freqSpin)
        self.toggledBmAction = self.createToggledBm()
        self.scaleAction = self.createScalePlotAction()
        self.tempAction = self.createTempDisplay()
        
        self.toolbar = self.addToolBar('Measurement')
        self.addActions(self.toolbar, (self.connectAction, self.connectThermoAction, None, self.startAction, self.recordAction, self.stopAction,
                                      None,self.selectChannelAction,None,self.tempAction,None,self.freqSpinAction,self.toggledBmAction,
                                      self.scaleAction))
    
    def test(self,val):
        print(val)
        
    def createScalePlotAction(self):
        wa = QtGui.QWidgetAction(self)
        
        self.minWlSpin = QtGui.QDoubleSpinBox()
        self.minWlSpin.setDecimals(3)
        self.minWlSpin.setSuffix(' nm')
        self.minWlSpin.setRange(1460.0,1619.0)
        self.minWlSpin.setValue(1500.0)
        self.minWlSpin.valueChanged.connect(self.scaleInputSpectrum)
        
        self.maxWlSpin = QtGui.QDoubleSpinBox()
        self.maxWlSpin.setDecimals(3)
        self.maxWlSpin.setSuffix(' nm')
        self.maxWlSpin.setRange(1461.0, 1620.0)
        self.maxWlSpin.setValue(1600.0)
        self.maxWlSpin.valueChanged.connect(self.scaleInputSpectrum)
        l = QtGui.QHBoxLayout()
        l.addWidget(self.minWlSpin)
        l.addWidget(QtGui.QLabel(text=' - '))
        l.addWidget(self.maxWlSpin)
        
        w = QtGui.QWidget()
        w.setLayout(l)
        wa.setDefaultWidget(w)
        
        return wa
        
    def createTempDisplay(self):
        a = QtGui.QWidgetAction(self)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.tempDisplay = QtGui.QLabel(text=u'T=-.- \u00b0C')
        self.tempDisplay.setFont(font)
        a.setDefaultWidget(self.tempDisplay)
        return a
    
    def createToggledBm(self):
        a = QtGui.QWidgetAction(self)
        #w = QtGui.QWidget()
        self.dBmCheck = QtGui.QCheckBox(text='dBm')
        self.dBmCheck.stateChanged.connect(self.showdBm)
        self.dBmCheck.setChecked(True)
        a.setDefaultWidget(self.dBmCheck)
        return a
        
    def getAllFromQueue(self, Q):
        """ Generator to yield one after the others all items 
            currently in the queue Q, without any waiting.
        """
        try:
            while True:
                yield Q.get_nowait( )
        except Queue.Empty:
            raise StopIteration


    def getItemFromQueue(self, Q, timeout=0.01):
        """ Attempts to retrieve an item from the queue Q. If Q is
            empty, None is returned.
            
            Blocks for 'timeout' seconds in case the queue is empty,
            so don't use this method for speedy retrieval of multiple
            items (use get_all_from_queue for that).
        """
        try: 
            item = Q.get(True, timeout)
        except Queue.Empty: 
            return None
        
        return item
        
    def getTemp(self):
        self.tc08usb.get_single()
        temp = self.tc08usb[1]
        tempStr = "T=" + str("{0:.1f}".format(temp)) + u' \u00b0C'
        self.tempDisplay.setText(tempStr)
        numVal = np.count_nonzero(self.__tempArray[0])
        if numVal < self.__maxTempBuffer:
            self.__tempArray[1][numVal] = temp
            self.__tempArray[0][numVal] = time()#-self.startMeasurementTime
        else:
            self.__tempArray[1] = shift(self.__tempArray[1], -1, cval = temp)
            self.__tempArray[0] = shift(self.__tempArray[0], -1, cval = time())#-self.startMeasurementTime)
             
        if numVal >1:
            tempA = np.array(self.__tempArray[:,:numVal-1])
            tempA[0] = tempA[0]-self.startMeasurementTime
            if self.plotTab.currentIndex() == 1:
                self.plotTrace.plotTemp(tempA)
        
    def initTempArray(self):
        self.__tempArray = np.zeros((2,self.__maxTempBuffer))
        
    
    def readDataFromQ(self):
        qData = list(list(self.getAllFromQueue(self.dataQ)))
        timestamp = 0
        d = None
        if len(qData) > 0:
            d = np.array(qData[-1][0])
            timestamp = qData[-1][1]
            d = d[:,self.__scalePos]
            return d, timestamp , 1
        else:
            return 0,0,0       
            
    def saveLastData(self, timestamp, numPeaks):
        if self.logFile:
            print('save Data')
            temp = self.tempDisplay.text()
            temp = temp.split(' ')
            _str = str(timestamp) + '\t' + str(temp[0]) + '\t'
            for i, chan in enumerate(self.channelList):
                peaks = self.__fbg.channels[chan-1].getLastValues(numPeaks[i])
                for val in peaks:
                    _str += str("{0:.3f}".format(val)) + '\t'
            _str = '\n'
            print(_str)
            self.logFile.write(_str)
            
    def scaleInputSpectrum(self):
        _min = float(self.minWlSpin.value())
        _max = float(self.maxWlSpin.value())
        if _min > _max:
            _min = _max-1
        if _max < _min:
            _max = _min+1
        self.__scalePos = np.where((self.__wavelength>=_min)&(self.__wavelength<=_max))[0]
        self.__scaledWavelength = self.__wavelength[self.__scalePos]
    
    def setActionState(self):
        if self.isConnected:
            if self.measurementActive:
                self.startAction.setEnabled(False)
                self.recordAction.setEnabled(True)
                self.stopAction.setEnabled(True)
            else:
                self.startAction.setEnabled(True)
                self.recordAction.setEnabled(False)
                self.stopAction.setEnabled(False)
        else:
            self.startAction.setEnabled(False)
            self.recordAction.setEnabled(False)
            self.stopAction.setEnabled(False)
            
    def setChannels(self):
        self.channelList = self.channelSelection.getChannelList()
        if self.Monitor:
            self.Monitor.setChannelList(self.channelList)
        self.plotSpec.setChannelList(self.channelList)
        
    def showdBm(self, state):
        if state:
            self.plotSpec.setdBm(True)
        else:
            self.plotSpec.setdBm(False)
            
    def startMeasurement(self):
        self.__fbg = FBGData()
        self.logFileName = strftime('%Y%m%d_%H%M%S') + '.log'
        self.logFile = open(self.logFileName,'w')
        self.plotTrace.initTraces([0,],0)
        self.__freq = self.freqSpin.value()
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.updateData)
        
        #initialize Queue
        self.dataQ = Queue.Queue(100)
        self.initTempArray()
        self.Monitor = MonitorHyperionThread(self.dataQ, self.si255, 
                                         self.channelList, specDevider=self.__freq)
        self.Monitor.start()
        self.updateTimer.setInterval(25*self.__freq)
            
        self.startMeasurementTime = time()
        self.initTempArray()
        self.lastTime = time()
        self.fps = None
            
        self.measurementActive = True
        self.setActionState()
        
        #start updateMonitor Timer
        self.updateTimer.start()
        
                
    def stopMeasurement(self):
        if self.__freq <10:
            self.Monitor.join(0.1)
            self.Monitor = None
            self.si255.disable_spectrum_streaming()
        
        self.measurementActive = False
        self.updateTimer.stop()
        self.setActionState()
        self.logFile.close()
        
    def toggleThermo(self):
        if self.connectThermoAction.isChecked():
            self.connectTemp()
        else:
            self.disconnectTemp()
    
    def updateData(self):
        numPeaks = 0
        data = np.zeros((1,1))
        data, timestamp, success  = self.readDataFromQ()
        actualTime = timestamp-self.startMeasurementTime
        if not success: return
        if len(data[:,0]) == len(self.channelList):
            numPeaks = self.__fbg.searchPeaks(self.__scaledWavelength, data,self.channelList, 
                                       self.channelSelection, actualTime)
        #print('Anzahl Peaks total :', sum(numPeaks))
        if self.plotTab.currentIndex() == 0:
            self.plotSpec.plotS(self.__scaledWavelength, data)
        else:
            self.plotTrace.plotTraces(self.channelList, numPeaks, self.__fbg)
            
        if self.recordAction.isChecked() and self.__freq >= 10:
            self.saveLastData(actualTime, numPeaks)

        dt = timestamp-self.lastTime
        if timestamp:
            if self.fps is None:
                self.fps = 1.0/dt
            else:
                s = np.clip(dt*3., 0, 1)
                self.fps = self.fps * (1-s) + (1.0/dt) * s
            self.statusBar().showMessage('%0.2f Hz' % (self.fps))
            self.lastTime = timestamp