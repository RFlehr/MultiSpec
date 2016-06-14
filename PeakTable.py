# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 21:37:33 2016

@author: Roman
"""

from pyqtgraph.Qt import QtGui

class PeakTable(QtGui.QTableWidget):
    def __init__(self, channelList = [1,], peakList = [1], parent=None):
        QtGui.QTableWidget.__init__(self, parent)
        
        self.__headerStr = 'FBG '
        self.__rowStr = 'Channel '
        self.__cL = channelList
        self.__pL = peakList
        
        self.__numCols = max(self.__pL)
        self.__numRows = len(self.__cL)
        
        self.initTable()
        print(self.__numCols, self.__numRows)
        
        
    def initTable(self):
        self.setColumnCount(self.__numCols)
        self.setRowCount(self.__numRows)
        for i in range(self.__numCols):
            for j in range(self.__numRows):
                self.setItem(j,i,QtGui.QTableWidgetItem('Test'))
        self.setHeader()
        self.setChanLabel()
        
    def setHeader(self):
        header = []        
        for i in range(self.__numCols):
            header.append(self.__headerStr +str(i+1))
        self.setHorizontalHeaderLabels(header)
        
    def setChanLabel(self):
        label = []
        for i in range(self.__numRows):
            label.append(self.__rowStr + str(self.__cL[i]))
        self.setVerticalHeaderLabels(label)
        
        
        
        
        
if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    pt = PeakTable([1,2],[3,5])
    pt.show()
    sys.exit(app.exec_())