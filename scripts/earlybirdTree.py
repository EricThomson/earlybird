# -*- coding: utf-8 -*-
"""
earlybirdTree.py: defines the EarlyBirdTree class:
Uses QStandardItemModel with QTreeView to make a simple, flexible to-do tree.

Check/uncheck (and need to have this part of load now too)
"""


import sys
import os
import json
from PySide import QtGui, QtCore
              
        
class StandardItemModel(QtGui.QStandardItemModel):
    '''
    Our standard item model will have a special signal for when items are edited
    '''
    itemDataChanged = QtCore.Signal(object, object, object, object)
    
    
class StandardItem(QtGui.QStandardItem):
    '''
    QStandardItem with setData reimplemented for placing edits on undostack, 
    as discussed at:
      http://stackoverflow.com/questions/29527610/how-to-undo-edit-of-qstandarditem-in-pyside-pyqt
    '''
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
    '''
    The earlyBird to do tree view.
    '''
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
        
        self.setStyleSheet("QTreeView::item:hover{background-color: #C9C9C9;}") #previous was yellowish #999966;}")  
        self.headerLabels = sorted(self.columnIndices.iterkeys(), key=lambda k: self.columnIndices[k])
        self.model.setHorizontalHeaderLabels(self.headerLabels) 
        self.setUniformRowHeights(True)  #Can make things a bit faster
        if self.filename:
            self.loadEarlybirdFile(self.filename)

    def makeConnections(self):
        self.model.itemDataChanged.connect(self.itemDataChangedSlot)
        self.clicked.connect(self.clickedSlot)

    def itemDataChangedSlot(self, item, oldValue, newValue, role):
        '''
        When any data is changed in an item, the itemDataChanged signal is 
        emitted, and calls this slot. This is used to pushed changes of
        existing items onto the undo stack. For details of this, see:
        http://stackoverflow.com/questions/29640408/how-to-treat-click-events-differently-for-an-items-checkbox-versus-its-text-p
        '''
        #print 'Itemdatachanged:', role, item.column(), oldValue, newValue #for debugging
        if role == QtCore.Qt.EditRole:  #when text is changed
            command = CommandTextEdit(self, item, oldValue, newValue,
                "Text changed from '{0}' to '{1}'".format(oldValue, newValue))
            self.undoStack.push(command)
            return True
        if role == QtCore.Qt.CheckStateRole:  #checkstate changed
            checkStateChangeCommand = CommandCheckStateChange(self, item, oldValue, newValue, 
                "CheckState changed from '{0}' to '{1}'".format(oldValue, newValue))
            self.undoStack.push(checkStateChangeCommand)
            return True  

    def clickedSlot(self, index):
        '''
        Whenever an item is clicked, this is called. This is used specifically to     
        handle clicks of + and - (add and remove tasks)
        '''
        if index.column() == self.columnIndices["+"]:
            self.addTask(index)
        if index.column() == self.columnIndices["-"]:
            #print "Remove item in row ", index.row()
            self.removeTask(self.model, index)


    def addTask(self, parentIndex = QtCore.QModelIndex()):
        '''       
        Add new task row to given parent.
        '''
        newNameItem = StandardItem("Double click to edit")
        if parentIndex.isValid(): #add to column 0 of parent
            parentNameIndex = self.model.index(parentIndex.row(), 0, parentIndex.parent()) 
            parentNameItem = self.model.itemFromIndex(parentNameIndex)
        else: #add to root item
            parentNameItem = self.rootItem
        newNameItem.setCheckable(True)
        newNameItem.setCheckState(QtCore.Qt.Unchecked)
        newTaskNameUserData = {"done": False}
        newNameItem.setData(newTaskNameUserData, role = QtCore.Qt.UserRole)
        newItemRow = self.makeTaskRow(newNameItem) 
        description = "Added child to {0}".format(parentNameItem.text())
        addCommand = CommandAddTask(self, parentNameItem, newItemRow, description)
        self.undoStack.push(addCommand)
       
    def removeTask(self, model, itemIndex = QtCore.QModelIndex()):
        '''
        Remove task with given index.
        '''
        parentIndex = itemIndex.parent()
        if parentIndex.isValid():
            parentItem = model.itemFromIndex(parentIndex)
        else:
            parentItem = self.rootItem
        taskItem = parentItem.child(itemIndex.row(), 0) #column 0
        description = "Removed '{0}' task.".format(taskItem.text())
        removeCommand = CommandRemoveTask(self, parentItem, taskItem, description)
        self.undoStack.push(removeCommand)
       
    '''
    ***
    Following three methods are used to move rows up and down
    ***
    '''
    def moveRowUp(self, index):  
        '''
        Moves selected row up with children attached if it has children,
        and only moves up within table it is in: not past parent
        '''
        sourceRowNum = index.row()
        if sourceRowNum > 0:
            targetRowNum = sourceRowNum - 1
            description = "Move up row {0}".format(sourceRowNum)
            moveUpCommand = CommandMoveRow(self, index.parent(),\
                                             sourceRowNum, targetRowNum, description)
            self.undoStack.push(moveUpCommand)

    def moveRowDown(self, index):  
        '''
        Moves selected row down with children attached if it has children,
        and only moves down within table it is in: not below next parent
        '''           
        numRows = self.model.rowCount(index.parent())
        sourceRowNum = index.row()
        if sourceRowNum < numRows - 1:
            targetRowNum = sourceRowNum + 1
            description = "Move row {0} down".format(sourceRowNum)
            moveDownCommand = CommandMoveRow(self, index.parent(),\
                                             sourceRowNum, targetRowNum, description)
            self.undoStack.push(moveDownCommand)
    
    def swapRows(self, parentIndex, rowNumber1, rowNumber2):
        '''
        Swaps two rows that have the same parent, highlights the
        content originally in rowNumber1. Is called by 
        the command classes.
        '''               
        if parentIndex.isValid():
            parentItem = self.model.itemFromIndex(parentIndex)
            if parentItem.rowCount() >= max([rowNumber1, rowNumber2]):
                sourceRowItems = parentItem.takeRow(rowNumber1)
                parentItem.insertRow(rowNumber2, sourceRowItems)
            else:
                return False
        else:  #top-level task
            sourceRowItems = self.model.takeRow(rowNumber1)
            self.model.insertRow(rowNumber2, sourceRowItems)
        #Following selects item moved to rowNumber2 from rowNumber1:
        selectIndex = self.model.index(rowNumber2, 0, parentIndex)
        self.selectionModel().clear()
        self.selectionModel().select(selectIndex, QtGui.QItemSelectionModel.Rows | QtGui.QItemSelectionModel.SelectCurrent)
        self.expandAll() #should just recursively expand sourceItem, not all
         
    '''
    ***
    Next four methods implement mechanics for loading .eb files
    ***
    '''
    def loadEarlybirdFile(self, filename = None):
        ''' 
        Opens eb file from memory and populates model with data.
        '''
        self.dirtySaveCheck()
        directoryName = os.path.dirname(filename) if filename else "."
        if not filename:
            filename, foo = QtGui.QFileDialog.getOpenFileName(None,
                    "Load earlybird file", directoryName, 
                    "(*.eb)")          
        if filename:
            with open(filename) as f:
                fileData = json.load(f) #loads data as dictionary
            if self.populateModel(fileData):
                self.filename = filename
                self.undoStack.clear()
                self.expandAll()
                for colNum in range(self.model.columnCount()):  #expands to viewed contents, so do after expansion
                    self.resizeColumnToContents(colNum)
                return True   
            else:
                print "{0} not loaded correctly".format(filename)  #Refactor to Dialog? 
        return False   
    
    def populateModel(self, fileData):
        '''
        Takes dictionary of eb data and loads tasks into model.
        '''
        if "tasks" not in fileData:
            return False 
        taskList = fileData["tasks"]
        self.clearModel()
        self.loadTasks(taskList, self.rootItem)
        return True
       
    def loadTasks(self, taskList, parentRow):
        '''
        Recursively load tasks until we hit a base task (a task w/o any subtasks).
        '''
        for (taskNum, task) in enumerate(taskList):
            taskNameItem = StandardItem(task["name"])
            taskNameItem.setCheckable(True)
            #print "task and done", task["name"], task["done"]  #for debugging
            if task["done"]:
                taskNameItem.setCheckState(QtCore.Qt.Checked)  
                self.strikeItem(taskNameItem)
            else:
                taskNameItem.setCheckState(QtCore.Qt.Unchecked)
            taskRow = self.makeTaskRow(taskNameItem)
            if parentRow is self.rootItem:
                parentRow.appendRow(taskRow)  
            else:
                parentRow[0].appendRow(taskRow) #add children only to column 0 
            if "tasks" in task:
                subtaskList = task["tasks"]
                self.loadTasks(subtaskList, taskRow) 

    def makeTaskRow(self, nameItem):
        '''
        Create a row for insertion in the model.
        '''
        taskRow = [None] * len(self.columnIndices)
        taskRow[self.columnIndices["Task"]] = nameItem
        taskRow[self.columnIndices["+"]] = StandardItem("+")
        taskRow[self.columnIndices["-"]] = StandardItem("-") 
        taskRow[self.columnIndices["+"]].setEditable(False)
        taskRow[self.columnIndices["-"]].setEditable(False)  
        return taskRow
        
    '''
    ****
    Next seven methods are part of the saving mechanics
    ****
    '''
    def dirtySaveCheck(self):
        '''
        Check to see if the file has been changed, and if it has, ask if the
        user wants to save changes. They can cancel, or save, or not save.
        '''
        if not self.undoStack.isClean():
            saveDialogResponse = self.saveChangesDialog()
            if saveDialogResponse == QtGui.QMessageBox.Cancel:
                return #false
            elif saveDialogResponse == QtGui.QMessageBox.Yes:  
                self.saveTodoData()  
    
    def saveChangesDialog(self):
        '''Ask if the user wants to save changes.'''
        return QtGui.QMessageBox.question(self,
                "Earlybird: Save changes?",
                "Save unsaved changes first?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
            
    def saveTodoData(self): 
        '''
        Save data from the tree as json formatted eb file
        '''
        if self.filename:
            dictModel = self.modelToDict()
            with open(self.filename, 'w') as fileToWrite:
                json.dump(dictModel, fileToWrite, indent=2)
        else:
            self.saveTodoDataAs()
        self.undoStack.clear()
            
    def saveTodoDataAs(self):
        '''
        Save data in model as ... json formatted eb file
        '''
        dir = os.path.dirname(self.filename) if self.filename is not None else "."
        self.filename, flt = QtGui.QFileDialog.getSaveFileName(None,
                "EarlyBird: Load data file", dir, "EarlyBird data (*.eb)")           
        if self.filename:
            print "Saving: ", self.filename #for debugging
            dictModel = self.modelToDict()
            with open(self.filename, 'w') as fileToWrite:
                json.dump(dictModel, fileToWrite, indent=2)
        self.undoStack.clear()
     
    def modelToDict(self):  
        '''
        Takes model presently in view, and saves all data as dictionary.
        Called by self.saveTodoData() and self.saveTodoDataAs()
        '''
        dictModel = {}       
        if self.rootItem.rowCount():           
            dictModel["tasks"]= self.createTaskList(self.rootItem)
            return dictModel
                        
    def createTaskList(self, parentItem):
        '''  
        Recursively traverses children creating list of dictionary-encoded tasks
        (name and done properties) to be saved as json
        '''
        childItemsList = self.getChildren(parentItem) #list of column 0 items (includes text/checkstate etc)
        numChildren = len(childItemsList)
        if numChildren > 0:
            childDictList = [None] * numChildren
            for (childNum, childItem) in enumerate(childItemsList):
                childDict = {}
                childDict["name"] = childItem.text()
                childDict["done"] = True if childItem.checkState() else False
                #now see if *this* child has children
                if childItem.rowCount():
                    childDict["tasks"] = self.createTaskList(childItem)
                childDictList[childNum] = childDict
            return childDictList
        else:
            return None
            
    def getChildren(self, parentItem):
        ''' 
        Returns list of child name items (column 0) of parentItem. Used by createTaskList.
        '''
        numChildren = parentItem.rowCount()
        if numChildren > 0:
            childItemList = [None] * numChildren
            for childNum in range(numChildren):
                childItemList[childNum] = parentItem.child(childNum, 0) #pulls column 0 
        else:
            childItemList = None
        return childItemList
        
    '''
    ***
    Other sundry methods follow
    ***
    '''   
    def clearModel(self):
        '''
        Clears data from model,clearing the view, but repopulates headers/root.
        Used whenever an eb file is loaded, or newFile method instantiated
        '''
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.headerLabels)
        self.rootItem = self.model.invisibleRootItem()   
        
    def newFile(self):
        '''
        Creates blank tree
        '''
        self.dirtySaveCheck()
        self.filename = None
        self.clearModel()
        self.undoStack.clear()
        
    def strikeItem(self, item):
        itemFont = item.font()
        itemFont.setStrikeOut(True)
        item.setFont(itemFont)   
        
    def unstrikeItem(self, item):
        itemFont = item.font()
        itemFont.setStrikeOut(False)
        item.setFont(itemFont)
        
    def closeEvent(self, event):
        '''Allows user to ignore close event.'''
        if not self.undoStack.isClean():
            saveDialogResponse = self.saveChangesDialog()
            if saveDialogResponse == QtGui.QMessageBox.Cancel:
                event.ignore()  #This is why you don't use checkDirtySave()
                return
            elif saveDialogResponse == QtGui.QMessageBox.Yes:
                self.saveTodoData()
        event.accept()
            

'''
***
Following are all the command classes for pushing commands onto (or pulling 
commands off of) the undo stack.
***
'''                  
class CommandMoveRow(QtGui.QUndoCommand):
    '''
    Moves row up among its siblings
    '''
    def __init__(self, view, parentIndex, sourceRowNum, targetRowNum, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.parentIndex = parentIndex
        self.sourceRowNum = sourceRowNum
        self.targetRowNum = targetRowNum
        self.view = view
    def redo(self):
        self.view.swapRows(self.parentIndex, self.sourceRowNum, self.targetRowNum)
    def undo(self):
        self.view.swapRows(self.parentIndex, self.targetRowNum, self.sourceRowNum)

        
class CommandRemoveTask(QtGui.QUndoCommand):
    '''
    Remove row from tree
    '''
    def __init__(self, view, parentItem, childItem, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.parentItem = parentItem
        self.view = view
        self.childRow = self.view.makeTaskRow(childItem)
        self.rowNumber  = childItem.row()
    def redo(self):
        self.parentItem.takeRow(self.rowNumber)
    def undo(self):
        self.parentItem.insertRow(self.rowNumber, self.childRow)
        self.view.expandAll() #could just recursively expand thsi node
        
    
class CommandAddTask(QtGui.QUndoCommand):
    '''
    Add new row to tree
    '''
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
    '''
    Undo/redo text edit changes
    
    The disconnect is needed to avoid infinite calls to itemDataChangedSlot:
      http://stackoverflow.com/questions/29527610/how-to-undo-edit-of-qstandarditem-in-pyside-pyqt
    Namely, itemDataChangedSlot would call this, but when this is called and text changed, then
    itemDataChangedSlot would be called again, and so on. To block this, disconnect the slot temporarily.
    '''
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
    '''
    Undoing/redo checkbox state changes
    
    For reasoning behind disconnect/connect, see docs for CommandTextEdit.
    '''
    def __init__(self, earlybirdTree, item, oldCheckState, newCheckState, description):
        QtGui.QUndoCommand.__init__(self, description)
        self.item = item
        self.tree = earlybirdTree
        self.oldCheckState = QtCore.Qt.Unchecked if oldCheckState == 0 else QtCore.Qt.Checked
        self.newCheckState = QtCore.Qt.Checked if oldCheckState == 0 else QtCore.Qt.Unchecked
    def redo(self):
        self.item.model().itemDataChanged.disconnect(self.tree.itemDataChangedSlot) 
        self.item.setCheckState(self.newCheckState)
        if self.newCheckState == QtCore.Qt.Checked:
            self.tree.strikeItem(self.item)
        else:
            self.tree.unstrikeItem(self.item)
        self.item.model().itemDataChanged.connect(self.tree.itemDataChangedSlot) 
    def undo(self):
        self.item.model().itemDataChanged.disconnect(self.tree.itemDataChangedSlot)
        self.item.setCheckState(self.oldCheckState)
        if self.oldCheckState == QtCore.Qt.Checked:
            self.tree.strikeItem(self.item)
        else:
            self.tree.unstrikeItem(self.item)
        self.item.model().itemDataChanged.connect(self.tree.itemDataChangedSlot) 

        
def main():
    ebApp = QtGui.QApplication(sys.argv)
    firstEb = EarlybirdTree(filename = "../tests/unit/properFormatTest.eb") #examples/simpleTree.eb")
    firstEb.show()
    undoView = QtGui.QUndoView(firstEb.undoStack)
    undoView.show()
    sys.exit(ebApp.exec_())


if __name__ == "__main__":
    main()
    
