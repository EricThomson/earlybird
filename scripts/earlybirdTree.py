# -*- coding: utf-8 -*-
"""
earlybirdTree.py: defines the EarlyBirdTree class:
Uses QStandardItemModel with QTreeView to make a simple, flexible to-do tree.

To do: 
-Add item functionality
   Basic functionality in earlybirdTree
       Task
       Task block
   Connect + column to this method for tasks
   Add button to main for adding task block
   Integrate into undo framework
   
-Remove item functionality
-Move item up methods
-Move item down methods
-Should be enough for now to start with daily schedule

"""


import sys
import os
import json
from PySide import QtGui, QtCore
              
        
class StandardItemModel(QtGui.QStandardItemModel):
    '''Our standard item model will have a special signal for when items are edited'''
    itemDataChanged = QtCore.Signal(object, object, object, object)
    
    
class StandardItem(QtGui.QStandardItem):
    def setData(self, newValue, role=QtCore.Qt.UserRole + 1):
        #print "setData called with role ", role  #for debugging
        if role == QtCore.Qt.EditRole:
            oldValue = self.data(role)
            QtGui.QStandardItem.setData(self, newValue, role)
            model = self.model()
            if model is not None and oldValue != newValue:
                model.itemDataChanged.emit(self, oldValue, newValue, role)
            return True
        if role == QtCore.Qt.CheckStateRole:
            oldValue = self.data(role)
            QtGui.QStandardItem.setData(self, newValue, role)            
            model = self.model()
            if model is not None and oldValue != newValue:                             
                model.itemDataChanged.emit(self, oldValue, newValue, role)
            return True
        QtGui.QStandardItem.setData(self, newValue, role)

        
class EarlybirdTree(QtGui.QTreeView):
    '''The earlyBird to do tree view.'''
    
    #Change column order with value, header label with key
    columnIndices = {"Task": 0 , "+": 1, "-": 2} 
                          
    def __init__(self, parent=None, filename = None):
        QtGui.QTreeView.__init__(self, parent=None)
        self.parent = parent
        self.filename = filename
        self.model = StandardItemModel()
        self.rootItem = self.model.invisibleRootItem()        
        self.setModel(self.model)
        self.makeConnections()
        self.undoStack = QtGui.QUndoStack(self)
        
        self.setStyleSheet("QTreeView::item:hover{background-color:#999966;}")  
        self.headerLabels = sorted(self.columnIndices.iterkeys(), key=lambda k: self.columnIndices[k])
        self.model.setHorizontalHeaderLabels(self.headerLabels) 
        if self.filename:
            self.loadEarlybirdFile(self.filename)

    def makeConnections(self):
        '''Connect all the signals-slots needed.'''
        self.model.itemDataChanged.connect(self.itemDataChangedSlot)

    def itemDataChangedSlot(self, item, oldValue, newValue, role):
        '''Slot used to push changes of existing items onto undoStack'''
        if role == QtCore.Qt.EditRole:
            command = CommandTextEdit(self, item, oldValue, newValue,
                "Text changed from '{0}' to '{1}'".format(oldValue, newValue))
            self.undoStack.push(command)
            return True
        if role == QtCore.Qt.CheckStateRole:
            command = CommandCheckStateChange(self, item, oldValue, newValue, 
                "CheckState changed from '{0}' to '{1}'".format(oldValue, newValue))
            self.undoStack.push(command)
            return True  
            
    '''
    ***
    Next five methods are part of mechanics for loading .eb files
    ***
    '''
    def loadEarlybirdFile(self, filename = None):
        '''Opens todo tree file (.eb) and populates model with data.'''
        if not self.undoStack.isClean() and self.saveChangesDialog():
            self.saveTodoData() 
        directoryName = os.path.dirname(filename) if filename else "."
        if not filename:
            filename, foo = QtGui.QFileDialog.getOpenFileName(None,
                    "Load earlybird file", directoryName, 
                    "(*.eb)")          
        if filename:
            with open(filename) as f:
                fileData = json.load(f)
            if self.populateModel(fileData, filename):
                self.expandAll()
                self.filename = filename
                self.undoStack.clear()
                return True        
        return False   
    
    def populateModel(self, fileData, filename):
        '''Verify that top-level items are blocks, and calls methods to load data.'''
        if "taskblocks" not in fileData:
            print "Warning: Cannot load {0}.\n"\
                  "Top level must contain taskblocks.".format(filename)
            return False 
        if "tasks" in fileData:
            print "Warning: only reads taskblocks from top level.\n"\
                  "Igorning top-level tasks in {0}.".format(filename)
        taskblockList = fileData["taskblocks"]
        self.clearModel()
        return self.loadTaskblocks(taskblockList)
        
    def loadTaskblocks(self, taskblockList):  
        '''Load task blocks into the model'''
        for (blockNum, taskblock) in enumerate(taskblockList): 
            blockNameItem = StandardItem(taskblock["blockname"])
            taskblockItem = self.makeItemRow(blockNameItem)           
            self.rootItem.appendRow(taskblockItem)
            if "tasks" in taskblock:
                taskList = taskblock["tasks"]
                self.loadTasks(taskList, taskblockItem) 
        return True      
       
    def loadTasks(self, taskList, parentItem):
        '''Recursively load tasks until we hit a base task (a task w/o any subtasks).'''
        for (taskNum, task) in enumerate(taskList):
            taskNameItem = StandardItem(task["name"])
            taskNameItem.setCheckable(True)
            #print "task and done", task["name"], task["done"]
            if task["done"]:
                taskNameItem.setCheckState(QtCore.Qt.Checked)           
            else:
                taskNameItem.setCheckState(QtCore.Qt.Unchecked)
            taskItem = self.makeItemRow(taskNameItem)
            parentItem[0].appendRow(taskItem) #add children only to column 0  
            if "tasks" in task:
                subtaskList = task["tasks"]
                return self.loadTasks(subtaskList, taskItem) 

    def makeItemRow(self, nameItem):
        '''Create a row for insertion in the model.'''
        itemRow = [None] * len(self.columnIndices)
        itemRow[self.columnIndices["Task"]] = nameItem
        itemRow[self.columnIndices["+"]] = StandardItem("+")
        itemRow[self.columnIndices["+"]].setEditable(False)
        itemRow[self.columnIndices["-"]] = StandardItem("-")         
        itemRow[self.columnIndices["-"]].setEditable(False)  
        return itemRow
        
    '''
    ****
    Next seven methods are part of the saving mechanics
    ***
    '''
    def saveChangesDialog(self):
        '''Ask if the user wants to save changes.'''
        if QtGui.QMessageBox.question(self,
                "Earlybird: Save changes?",
                "Save unsaved changes first?",
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            return True
        else:
            return False
            
    def saveTodoData(self): 
        '''Save data from the tree in json format'''
        if self.filename:
            dictModel = self.modelToDict()
            with open(self.filename, 'w') as fileToWrite:
                json.dump(dictModel, fileToWrite, indent=2)
        else:
            self.saveTodoDataAs()
        self.undoStack.clear()
            
    def saveTodoDataAs(self):
        '''Save data in model as...x'''
        dir = os.path.dirname(self.filename) if self.filename is not None else "."
        self.filename, flt = QtGui.QFileDialog.getSaveFileName(None,
                "EarlyBird: Load data file", dir, "EarlyBird data (*.eb)")           
        if self.filename:
            print "Saving: ", self.filename #for debugging
            dictModel = self.modelToDict()
            with open(self.filename, 'w') as fileToWrite:
                json.dump(dictModel, fileToWrite, indent=2)
        self.undoStack.clear()

     
    def modelToDict(self):  #def modelToDict(self, parentItem = self.rootItem):
        '''Takes model presently in view, and saves all data as dictionary.
        Called by self.saveTodoData() and self.saveTodoDataAs()'''
        dictModel = {}       
        if self.rootItem.rowCount():           
            dictModel["taskblocks"]= self.createTaskblockList(self.rootItem)
            return dictModel
            
    def createTaskblockList(self, parentItem):
        '''Creates list of task blocks, and their tasks (latter using createTasklist).
        Called by modelToDict which is used to save the model as a dictionary'''
        numChildren = parentItem.rowCount()
        if numChildren:
            taskblockList = [None] * numChildren
            childList = self.getChildren(parentItem)
            for childNum in range(numChildren):
                childItem = childList[childNum]
                childTaskblockData = {}
                childTaskblockData["blockname"]=childItem.text()               
                #now see if the block has children (tasks)
                if childItem.rowCount():
                    childTaskblockData["tasks"] = self.createTaskList(childItem)
                taskblockList[childNum] = childTaskblockData
            return taskblockList
        else:
            return None

    def createTaskList(self, parentItem):
        '''Recursively traverses model creating list of tasks to
        be saved as json'''
        numChildren = parentItem.rowCount()
        if numChildren:
            taskList = [None] * numChildren
            childList = self.getChildren(parentItem)
            for childNum in range(numChildren):
                childItem = childList[childNum]
                childTaskData = {}
                childTaskData["name"] = childItem.text()
                childTaskData["done"] = True if childItem.checkState() else False
                #now see if the present child has children
                if childItem.rowCount():
                    childTaskData["tasks"] = self.createTaskList(childItem)
                taskList[childNum] = childTaskData
            return taskList
        else:
            return None
            
    def getChildren(self, parentItem):
        '''Returns list of child items of parentItem. Used when converting
        model to dictionary for saving as json'''
        numChildren = parentItem.rowCount()
        if numChildren > 0:
            childItemList = [None] * numChildren
            for childNum in range(numChildren):
                childItemList[childNum] = parentItem.child(childNum, 0)
        else:
            childItemList = None
        return childItemList
        
    '''Other sundry methods follow'''
    def clearModel(self):
        '''Clears data from model,clearing the view, but repopulates headers/root.
        Used whenever an .eb file is loaded, or newFile method instantiated'''
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.headerLabels)
        self.rootItem = self.model.invisibleRootItem()   
        
    def newFile(self):
        '''Creates blank tree'''
        if not self.undoStack.isClean() and self.saveChangesDialog():
            self.saveTodoData()
        self.filename = None
        self.clearModel()
        self.undoStack.clear()
       
    def closeEvent(self, event):
        '''Typically closeevent is called by a QMainWindow wrapper (the top-level
        window of the app, but sometimes we do view these guys standalone, so this
        could be helpful for that.'''
        if not self.undoStack.isClean() and self.saveChangesDialog():
            self.fileSave()
        self.close()


class CommandTextEdit(QtGui.QUndoCommand):
    '''Command for undoing/redoing text edit changes, to be placed in undostack'''
    def __init__(self, earlybirdTree, item, oldText, newText, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.item = item
        self.tree = earlybirdTree
        self.oldText = oldText
        self.newText = newText

    def redo(self):      
        self.item.model().itemDataChanged.disconnect(self.tree.itemDataChangedSlot) 
        self.item.setText(self.newText)
        self.item.model().itemDataChanged.connect(self.tree.itemDataChangedSlot) 

    def undo(self):
        self.item.model().itemDataChanged.disconnect(self.tree.itemDataChangedSlot) 
        self.item.setText(self.oldText)
        self.item.model().itemDataChanged.connect(self.tree.itemDataChangedSlot) 
        

class CommandCheckStateChange(QtGui.QUndoCommand):
    '''Command for undoing/redoing check state changes, to be placed in undostack'''
    def __init__(self, earlybirdTree, item, oldCheckState, newCheckState, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.item = item
        self.tree = earlybirdTree
        self.oldCheckState = QtCore.Qt.Unchecked if oldCheckState == 0 else QtCore.Qt.Checked
        self.newCheckState = QtCore.Qt.Checked if oldCheckState == 0 else QtCore.Qt.Unchecked

    def redo(self):
        self.item.model().itemDataChanged.disconnect(self.tree.itemDataChangedSlot) 
        self.item.setCheckState(self.newCheckState)
        self.item.model().itemDataChanged.connect(self.tree.itemDataChangedSlot) 
        
    def undo(self):
        self.item.model().itemDataChanged.disconnect(self.tree.itemDataChangedSlot)
        self.item.setCheckState(self.oldCheckState)
        self.item.model().itemDataChanged.connect(self.tree.itemDataChangedSlot) 

        
def main():
    ebApp = QtGui.QApplication(sys.argv)
    firstEb = EarlybirdTree(filename = "../tests/unit/blockOnlyTest.eb")
    firstEb.show()
    undoView = QtGui.QUndoView(firstEb.undoStack)
    undoView.show()
    sys.exit(ebApp.exec_())


if __name__ == "__main__":
    main()
    
