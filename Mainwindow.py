# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:36:45 2016

@author: Flehr
"""

__title__ =  'MultiSpec'
__about__ = """Hyperion si255 Interrogation Software
            including Pico Temprature measurements
            """
__version__ = '0.1.1'
__date__ = '01.03.2016'
__author__ = 'Roman Flehr'
__cp__ = u'\u00a9 2016 Loptek GmbH & Co. KG'

import sys
sys.path.append('../')

from pyqtgraph.Qt import QtGui, QtCore
import plot as pl
import Monitor as mon
import hyperion, Queue, time#, os
import numpy as np
#from tc08usb import TC08USB, USBTC08_TC_TYPE, USBTC08_ERROR#, USBTC08_UNITS

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
        self.Monitor = None
        
        self.measurementActive = False
        
        self.plotSpec = pl.Plot(self.channelList)
        self.plotTab = QtGui.QTabWidget()
        self.plotTab.addTab(self.plotSpec,'Spectra')
        
        self.setWindowTitle(__title__ + ' ' + __version__)
        
        self.setCentralWidget(self.plotTab)
        
        #init menu
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
                #if self.tempConnected:
                #    self.tc08usb.close_unit()
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
        #except:
            #print('err: ',err)
            #pass
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
                                            icon='Button Close',tip='Close App')

        self.connectAction = self.createAction('&Connect', slot=self.connectHyperion,
                                              tip='Connect Spectrometer', checkable = True,
                                              icon='Button Add')        
        
        self.startAction = self.createAction('St&art', slot=self.startMeasurement, shortcut='Ctrl+M',
                                             tip='Start Measurement', icon='Button Play')
        
        self.stopAction = self.createAction('St&op', slot=self.stopMeasurement, shortcut='Ctrl+T',
                                        tip='Stop Measurment', icon='Button Stop')
        
        self.channelSelection = ChannelSelection()
        self.channelSelection.selectionChanged.connect(self.setChannels)
        self.selectChannelAction = QtGui.QWidgetAction(self)
        self.selectChannelAction.setDefaultWidget(self.channelSelection)
        self.toggledBmAction = self.createToggledBm()
        self.scaleAction = self.createScalePlotAction()
        
        self.toolbar = self.addToolBar('Measurement')
        self.addActions(self.toolbar, (self.connectAction, None, self.startAction, self.stopAction,
                                      None,self.selectChannelAction,None,self.toggledBmAction,
                                      self.scaleAction))
        
    def createScalePlotAction(self):
        wa = QtGui.QWidgetAction(self)
        
        self.minWlSpin = QtGui.QDoubleSpinBox()
        self.minWlSpin.setDecimals(3)
        self.minWlSpin.setSuffix(' nm')
        self.minWlSpin.setRange(1460.0,1619.0)
        self.minWlSpin.setValue(1540.0)
        self.minWlSpin.valueChanged.connect(self.scaleInputSpectrum)
        
        self.maxWlSpin = QtGui.QDoubleSpinBox()
        self.maxWlSpin.setDecimals(3)
        self.maxWlSpin.setSuffix(' nm')
        self.maxWlSpin.setRange(1469.0, 1620.0)
        self.maxWlSpin.setValue(1570.0)
        self.maxWlSpin.valueChanged.connect(self.scaleInputSpectrum)
        l = QtGui.QHBoxLayout()
        l.addWidget(self.minWlSpin)
        l.addWidget(QtGui.QLabel(text=' - '))
        l.addWidget(self.maxWlSpin)
        
        w = QtGui.QWidget()
        w.setLayout(l)
        wa.setDefaultWidget(w)
        
        return wa
    
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
        
    def readDataFromQ(self):
        """
        called by updateTimer
        """
        qData = list(list(self.getAllFromQueue(self.dataQ)))
        timestamp = 0
        if len(qData) > 0:
            d = np.array(qData[-1][0])
            timestamp = qData[-1][1]
            d = d[:,self.__scalePos]
            self.plotSpec.plotS(self.__scaledWavelength, d)
            
        dt = timestamp-self.lastTime
        if timestamp:
            if self.fps is None:
                self.fps = 1.0/dt
            else:
                s = np.clip(dt*3., 0, 1)
                self.fps = self.fps * (1-s) + (1.0/dt) * s
            self.statusBar().showMessage('%0.2f Hz' % (self.fps))
            self.lastTime = timestamp
    
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
                self.stopAction.setEnabled(True)
            else:
                self.startAction.setEnabled(True)
                self.stopAction.setEnabled(False)
        else:
            self.startAction.setEnabled(False)
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
        #initialize Queues
        self.dataQ = Queue.Queue()
        self.errorQ = Queue.Queue()
           
        self.Monitor = mon.MonitorThread(self.dataQ, self.errorQ, self.si255, self.channelList)
        self.Monitor.start()
        
        self.lastTime = time.time()
        self.fps = None
        #comError = self.getItemFromQueue(self.errorQ)
        #if comError is not None:
        #    QtGui.QMessageBox.critical(self,'iMon Connection Error',str(comError))
        #    self.iMonMonitor = None
            
        self.measurementActive = True
        self.setActionState()
        
        #start updateMonitor Timer
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.updateData)
        self.updateTimer.start(25)
        
                
    def stopMeasurement(self):
        self.Monitor.join(0.1)
        self.measurementActive = False
        self.updateTimer.stop()
        self.Monitor = None
        self.si255.disable_spectrum_streaming()
        
        self.setActionState()
        
    def updateData(self):
        self.readDataFromQ() 
       
        
class ChannelSelection(QtGui.QWidget):
    selectionChanged = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.channelList = []
        colorArray = ["color: blue", "color: red", "color: green", "color: black"]
        
        lay = QtGui.QHBoxLayout(self)
        lay.addWidget(QtGui.QLabel(text='Channel: '))
        self.checkArray = []
        for i in range(4):
            label = 'Ch' + str(i+1)
            l = QtGui.QLabel(text=label)
            l.setStyleSheet(colorArray[i])
            c = QtGui.QCheckBox()
            c.stateChanged.connect(self.updateChannelList)
            c.setStyleSheet(colorArray[i])
            self.checkArray.append(c)
            lay.addWidget(l)
            lay.addWidget(c)
        self.checkArray[0].setChecked(True)
        
    def getChannelList(self):
        return self.channelList
        
    def updateChannelList(self):
        self.channelList = []
        for i in range(4):
            if self.checkArray[i].isChecked():
                self.channelList.append(i+1)
        self.selectionChanged.emit()
        

        
        