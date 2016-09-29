# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 09:54:44 2016

@author: Flehr
"""
from pyqtgraph.Qt import QtGui, QtCore

class ChannelSelection(QtGui.QWidget):
    selectionChanged = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.channelList = []
        colorArray = ["color: blue", "color: red", "color: green", "color: black"]
        
        lay = QtGui.QGridLayout(self)
        lay.addWidget(QtGui.QLabel(text='Channel: '),0,0)
        lay.addWidget(QtGui.QLabel(text='Peaks: '),1,0)
        self.checkArray = []
        self.numPeaksLineArray = []
        for i in range(4):
            label = 'Ch' + str(i+1)
            l = QtGui.QLabel(text=label)
            l.setStyleSheet(colorArray[i])
            c = QtGui.QCheckBox()
            c.stateChanged.connect(self.updateChannelList)
            c.setStyleSheet(colorArray[i])
            self.checkArray.append(c)
            ed = QtGui.QLineEdit()
            ed.setReadOnly(True)
            ed.setAlignment(QtCore.Qt.AlignCenter)
            ed.setText('0')
            ed.setMaximumWidth(30)
            self.numPeaksLineArray.append(ed)
            lay.addWidget(l,0,2*i+1)
            lay.addWidget(c,0,2*i+2)
            lay.addWidget(ed,1,2*i+1,1,2)
        self.checkArray[0].setChecked(True)
        
    def getChannelList(self):
        return self.channelList
        
    def updateChannelList(self):
        self.channelList = []
        for i in range(4):
            isChecked = self.checkArray[i].isChecked()
            self.numPeaksLineArray[i].setEnabled(isChecked)
            if isChecked:
                self.channelList.append(i+1)
            else:
                self.numPeaksLineArray[i].setText(str(0))
        self.selectionChanged.emit()
        
    def setNumPeaksCh(self, channel , numPeaks):
        self.numPeaksLineArray[channel-1].setText(str(numPeaks))
    
    def setNumPeaks(self, numPeaksArray):
        np = numPeaksArray
        for i, num in enumerate(np):
            self.numPeaksLineArray[i].setText(str(num))

class FreqSpin(QtGui.QDoubleSpinBox):
    def __init__(self,parent=None):
        QtGui.QDoubleSpinBox.__init__(self,parent)
        
        self.setSingleStep(1)
        self.setRange(1,1e6)
        self.setValue(1)
        self.setMaximumWidth(80)
        
    def textFromValue(self, val):
        if val == 0: val = 1.
        freq = 10.0/val
        st = str("{0:.3f}".format(freq)) + ' Hz'
        return st
        
    def valueFromText(self, text):
        return int(10/float(text))  
        
class FreqSpinAction(QtGui.QWidgetAction):
    def __init__(self, parent=None):
        QtGui.QWidgetAction.__init__(self,parent)
        
        self.intLine = QtGui.QLineEdit()
        self.intLine.setMaximumWidth(45)
        self.intLine.returnPressed.connect(self.setFrequency)
                
        self.freq = FreqSpin()
        self.freq.valueChanged.connect(self.setIntervall)
        
        w = QtGui.QWidget()
        lay = QtGui.QGridLayout()
        w.setLayout(lay)
        w.setMaximumWidth(150)
        
        lay.addWidget(QtGui.QLabel(text='Interval'),0,0)
        lay.addWidget(QtGui.QLabel(text='Frequency'),0,1)
        lay.addWidget(self.intLine,1,0)
        lay.addWidget(self.freq,1,1)

        self.setDefaultWidget(w)
        self.setIntervall()


    def value(self):
        return int(self.freq.value())
        
    def setIntervall(self):
        interv = self.freq.value()*0.1
        _str = str(interv) + ' s'
        self.intLine.setText(_str)
        
    def setFrequency(self):
        _str = self.intLine.text()
        _str = _str.split(' ')[0]
        freq = int(float(_str)*10)
        self.freq.setValue(freq)