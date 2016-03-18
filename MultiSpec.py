# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:34:53 2016

@author: Flehr
"""

from pyqtgraph.Qt import QtGui
import sys

import Mainwindow as mw

app = QtGui.QApplication(sys.argv)
app.setStyle('windows')
spectra = mw.MainWindow()
spectra.show()
app.exec_()
