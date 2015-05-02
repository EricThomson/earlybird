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
   
   Integrate into undo framework (basically implement in undo right?)
   the question is this: do I need to implement the change *and* add it
   to the undo stack, or is it enough to just push it onto the undo stack?
   For checkstate and edits I think I had to do it with setData. With this
   I'm not as sure, as I am implementing the change. From Summerfield's it
   seems it is sufficient to pass it on to the undo stack.
   
   Summerfield add slot is this:
   
       def add(self):
        row = self.listWidget.currentRow()
        title = "Add %s" % self.name
        string, ok = QInputDialog.getText(self, title, "&Add")
        if ok and string:
            command = CommandAdd(self.listWidget, row, string,
                                 "Add (%s)" % string)
            self.undoStack.push(command)
            
        #and commandadd:
        class CommandAdd(QUndoCommand):
        
            def __init__(self, listWidget, row, string, description):
                super(CommandAdd, self).__init__(description)
                self.listWidget = listWidget
                self.row = row
                self.string = string
                self.setText(description)  #sets text of qundo *description* 
        
            def redo(self):
                self.listWidget.insertItem(self.row, self.string)
                self.listWidget.setCurrentRow(self.row)
        
            def undo(self):
                self.listWidget.takeItem(self.row)
        
   
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
            #Following not needed? as putting stuff on undostack already enacts the change!
            #Ask about this.Because if you mark out the same in checkstaterole, you
            #don't even end up with a checkbox!
            #
            #Should it be needed, is the question....
            #From overview of Qt's undo framework:
            #
            #The Command pattern is based on the idea that all editing in an 
            #application is done by creating instances of command objects. 
            #Command objects apply changes to the document and are stored 
            #on a command stack. Furthermore, each command knows how to undo 
            #its changes to bring the document back to its previous state. 
            #As long as the application only uses command objects to change 
            #the state of the document, it is possible to undo a sequence of 
            #commands by traversing the stack downwards and calling undo on 
            #each command in turn. It is also possible to redo a sequence 
            #of commands by traversing the stack upwards and calling redo 
            #on each command.
            
            QtGui.QStandardItem.setData(self, newValue, role) #this isn't actually needed!
            
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
            print "add item"
            self.addTask(index)
        if index.column() == self.columnIndices["-"]:
            print "Remove item"
            #self.removeRow(index)
            #self.modelChanged = True

    def addTask(self, parentIndex = QtCore.QModelIndex()):
        '''Add subtask to clicked item, which is the parent'''
        if parentIndex.isValid():
            parentNameIndex = self.model.index(parentIndex.row(), 0, parentIndex.parent()) #add to column 0
            parentNameItem = self.model.itemFromIndex(parentNameIndex)
        else:
            parentNameItem = self.rootItem
        newTask = StandardItem("Double click to edit")
        newTask.setCheckable(True)
        newTask.setCheckState(QtCore.Qt.Unchecked)
        taskUserData ={"done": False}
        newTask.setData(taskUserData, role = QtCore.Qt.UserRole)
        newTaskRow = self.makeItemRow(newTask) 
        description = "Added child to {0}".format(parentNameItem.text())
        addCommand = CommandAddTask(self, parentNameItem, newTaskRow, description)
        self.undoStack.push(addCommand)
        
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
        if not self.undoStack.isClean() and self.saveChangesDialog():
            self.fileSave()
        self.close()

class CommandAddTask(QtGui.QUndoCommand):
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
    
