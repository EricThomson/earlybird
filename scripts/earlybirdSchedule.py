# -*- coding: utf-8 -*-
"""
Created on Sun May 24 20:45:25 2015

@author: Eric

To do:
Bold time text...
Print main window

"""

import sys
from PySide import QtGui, QtCore
from earlybirdTree import EarlybirdTree

class DailyPlanner(QtGui.QMainWindow):
           
    def __init__(self, parent = None, filename = None):
        QtGui.QMainWindow.__init__(self, parent) 
        self.treeView = EarlybirdTree(filename = filename)
        self.schedule = ScheduleTable()

        self.mainSplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.mainSplitter.addWidget(self.treeView)
        self.mainSplitter.addWidget(self.schedule)
        self.setCentralWidget(self.mainSplitter)
        self.show()
        
class ScheduleTable(QtGui.QTableWidget):
    def __init__(self, parent=None):
        QtGui.QTableWidget.__init__(self, parent)
        self.setRowCount(17)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Time', 'Task'])
        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()
        self.fillTable()

        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(True)
                
    def fillTable(self):
        timeStrings = (' 7am', ' 8am', ' 9am', ' 10am', ' 11am', ' 12pm  ', ' 1pm' , ' 2pm',
                       ' 3pm', ' 4pm', ' 5pm', ' 6pm', ' 7pm',  ' 8pm', ' 9pm', ' 10pm', ' 11pm')
        for (timeNum, timeStr) in enumerate(timeStrings):
            timeItem = QtGui.QTableWidgetItem(timeStr)
            timeItem.setFlags(~QtCore.Qt.ItemIsEditable)
            itemFont = timeItem.font()
            itemFont.setBold(True)
            timeItem.setFont(itemFont)
            self.setItem(timeNum, 0, timeItem)   

    
def main():
    app = QtGui.QApplication(sys.argv)
    #mySchedule = ScheduleTable()
    #mySchedule.show()
    myDay = DailyPlanner(filename = "../working/workingWeekly.eb")
    myDay.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()