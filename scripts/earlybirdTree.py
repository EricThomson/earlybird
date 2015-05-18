# -*- coding: utf-8 -*-
"""
earlybirdTree.py: defines the EarlyBirdTree class:
Uses QStandardItemModel with QTreeView to make a simple, flexible to-do tree.

#Nomenclature:
#general (block or task)
#  nameItem/newNameItem
#  itemRow/newItemRow 
#Task Only
#  taskRow/ newTaskRow
#  taskNameItem / newTaskNameItem
#Block only
#  blockNameItem / newBlockNameItem
#  blockRow / newBlockRow


=========
After doing remove and add functionality, refactor that shit all up in there.
-Move item up methods
-Move item down methods
-Obvious cosmetic:
    -Column widths set automatically
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
            QtGui.QStandardItem.setData(self, newValue, role) #why needed?          
            model = self.model()
            if model is not None and oldValue != newValue:
                model.itemDataChanged.emit(self, oldValue, newValue, role)
            return True
        if role == QtCore.Qt.CheckStateRole:
            oldValue = self.data(role)
            QtGui.QStandardItem.setData(self, newValue, role)  #why?          
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
        QtGui.QTreeView.__init__(self, parent)
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
        self.clicked.connect(self.clickedSlot)

    def itemDataChangedSlot(self, item, oldValue, newValue, role):
        '''Slot used to push changes of existing items onto undoStack'''
        if role == QtCore.Qt.EditRole:
            command = CommandTextEdit(self, item, oldValue, newValue,
                "Text changed from '{0}' to '{1}'".format(oldValue, newValue))
            self.undoStack.push(command)
            return True
        if role == QtCore.Qt.CheckStateRole:
            checkStateChangeCommand = CommandCheckStateChange(self, item, oldValue, newValue, 
                "CheckState changed from '{0}' to '{1}'".format(oldValue, newValue))
            self.undoStack.push(checkStateChangeCommand)
            return True  

    def clickedSlot(self, index):
        '''Handles slots associated with + and - (item add and remove)'''
        if index.column() == self.columnIndices["+"]:
            self.addItem(index)
        if index.column() == self.columnIndices["-"]:
            print "Remove item in row ", index.row()
            self.removeItem(self.model, index)
            #self.removeRow(index)
            #self.modelChanged = True

    def addItem(self, parentIndex = QtCore.QModelIndex()):
        '''Add new row to parent'''
        newNameItem = StandardItem("Double click to edit")
        if parentIndex.isValid(): #Make a task
            parentNameIndex = self.model.index(parentIndex.row(), 0, parentIndex.parent()) #add to column 0
            parentNameItem = self.model.itemFromIndex(parentNameIndex)
            newNameItem.setCheckable(True)
            newNameItem.setCheckState(QtCore.Qt.Unchecked)
            newTaskNameUserData ={"done": False}
            newNameItem.setData(newTaskNameUserData, role = QtCore.Qt.UserRole)
        else:  #Make a block
            parentNameItem = self.rootItem
        newItemRow = self.makeItemRow(newNameItem) 
        description = "Added child to {0}".format(parentNameItem.text())
        addCommand = CommandAddItem(self, parentNameItem, newItemRow, description)
        self.undoStack.push(addCommand)
       
    def removeItem(self, model, itemIndex = QtCore.QModelIndex()):
        '''Remove clicked item'''
        parentIndex = itemIndex.parent()
        if parentIndex.isValid():
            parentItem = model.itemFromIndex(parentIndex)
            taskItem = parentItem.child(itemIndex.row(), 0)
            description = "Removed '{0}' task".format(taskItem.text())
        else:
            parentItem = self.rootItem
            taskItem = parentItem.child(itemIndex.row(), 0)
            description = "Removed '{0}' block.".format(taskItem.text())
        removeCommand = CommandRemoveItem(self, parentItem, taskItem, description)
        self.undoStack.push(removeCommand)
       

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
            blockRow = self.makeItemRow(blockNameItem)           
            self.rootItem.appendRow(blockRow)
            if "tasks" in taskblock:
                taskList = taskblock["tasks"]
                self.loadTasks(taskList, blockRow) 
        return True      
       
    def loadTasks(self, taskList, parentRow):
        '''Recursively load tasks until we hit a base task (a task w/o any subtasks).'''
        for (taskNum, task) in enumerate(taskList):
            taskNameItem = StandardItem(task["name"])
            taskNameItem.setCheckable(True)
            #print "task and done", task["name"], task["done"]
            if task["done"]:
                taskNameItem.setCheckState(QtCore.Qt.Checked)           
            else:
                taskNameItem.setCheckState(QtCore.Qt.Unchecked)
            taskRow = self.makeItemRow(taskNameItem)
            parentRow[0].appendRow(taskRow) #add children only to column 0  
            if "tasks" in task:
                subtaskList = task["tasks"]
                return self.loadTasks(subtaskList, taskRow) 

    def makeItemRow(self, nameItem):
        '''Create a row for insertion in the model.'''
        itemRow = [None] * len(self.columnIndices)
        itemRow[self.columnIndices["Task"]] = nameItem
        itemRow[self.columnIndices["+"]] = StandardItem("+")
        itemRow[self.columnIndices["-"]] = StandardItem("-") 
        itemRow[self.columnIndices["+"]].setEditable(False)
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
            dictModel["taskblocks"]= self.createBlockList()
            return dictModel
            
    def createBlockList(self):
        '''Return list of dictionary-encoded blocks. Each block
        also includes tasks curried from createTaskList()'''
        blockNameItemList = self.getChildren(self.rootItem) #list of block name items without any children
        numBlocks = len(blockNameItemList)
        if numBlocks > 0:
            blockNameDictList = [None]*numBlocks
            for (blockNum, blockNameItem) in enumerate(blockNameItemList):
                blockNameDict = {}  #create dictionary entry corresponding to each task block
                blockNameDict["blockname"] = blockNameItem.text()               
                #now see if the block has children (tasks)
                if blockNameItem.rowCount():
                    blockNameDict["tasks"] = self.createTaskList(blockNameItem)
                blockNameDictList[blockNum] = blockNameDict
            return blockNameDictList
        else:
            return None
            
    def createTaskList(self, parentItem):
        '''Recursively traverses model creating list of dictionary-encoded tasks to
        be saved as json'''
        taskNameList = self.getChildren(parentItem) 
        numChildren = len(taskNameList)
        if numChildren > 0:
            taskNameDictList = [None] * numChildren
            for (childNum, childNameItem) in enumerate(taskNameList):
                taskNameDict = {}
                taskNameDict["name"] = childNameItem.text()
                taskNameDict["done"] = True if childNameItem.checkState() else False
                #now see if *this* task has children
                if childNameItem.rowCount():
                    taskNameDict["tasks"] = self.createTaskList(childNameItem)
                taskNameDictList[childNum] = taskNameDict
            return taskNameDictList
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
        if not self.undoStack.isClean() and self.saveChangesDialog():
            self.fileSave()
        self.close()


class CommandRemoveItem(QtGui.QUndoCommand):
    '''Command to remove row from tree is pushed onto undo stack
       will this aappropriately remove children of child too?
       
       Doesn't seem to be working for blocks.
       
       Doesn't seem to expand.
       
       Don't like parentItem or (especially) childItem names'''
    def __init__(self, view, parentItem, childItem, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.parentItem = parentItem
        self.view = view
        self.childRow = self.view.makeItemRow(childItem)
        self.rowNumber  = childItem.row()
       
    def redo(self):
        self.parentItem.takeRow(self.rowNumber)
       
    def undo(self):
        self.parentItem.insertRow(self.rowNumber, self.childRow)
        self.view.expandAll() #could just recursively expand thsi node
        
        

#Nomenclature:
#general (block or task)
#  nameItem/newNameItem
#  itemRow/newItemRow 
#Task Only
#  taskRow/ newTaskRow
#  taskNameItem / newTaskNameItem
#Block only
#  blockNameItem / newBlockNameItem
#  blockRow / newBlockRow

class CommandAddItem(QtGui.QUndoCommand):
    '''Command to add new row to parent item is pushed onto undo stack'''
    def __init__(self, view, parentItem, newTaskRow, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.parentItem = parentItem
        self.newTaskRow = newTaskRow
        self.view = view
    def redo(self):
        self.parentItem.appendRow(self.newTaskRow)
        self.view.expand(self.parentItem.index())
    def undo(self):
        self.parentItem.takeRow(self.newTaskRow[0].row())
          
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
    
