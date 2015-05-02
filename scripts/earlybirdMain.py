# -*- coding: utf-8 -*-
"""
earlybirdMain.py
    A wrapper for the EarlybirdTree class that allows for user interaction
    with a to do tree.
    
Early bird to do tree. 
Because lists are bullshit.

=====
To do:
1. Pick a better default folder.
A. File/toolbar organization: Help /Version number (build in to class)
B. Add ability to print tree.
C. Add 'notes' above and below, which are text editor/files that are not part of the tree.
Like my monthly things and such.
D. Let user select color for taskblock with a menu button. Have color start as default white instead
of what you are doing now. Let user select color of blocks. And then save/load this make sure
the save/load of color works.
    -Have selected row take on just slightly ligher color within block
    -When you built by hand and then open a file, the color vals don't work quite right (e.g., 
     pink taskblock, then open a new guy, it will also have the first task block pink).




"""
import sys
import os
from PySide import QtGui, QtCore
from earlybirdTree import EarlybirdTree

class EarlybirdMain(QtGui.QMainWindow):
    '''Main window to wrap an EarlybirdTree'''
    def __init__(self, filename = None):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose) 
        self.view = EarlybirdTree(self, filename) 
        self.model = self.view.model
        self.windowTitleSet()
        self.setCentralWidget(self.view)
        self.createStatusBar()
        self.createActions()
        self.createToolbars()
        self.createMenus()
        self.setWindowIcon(QtGui.QIcon('../images/ebSun.png'))
       
    def createToolbars(self):
        '''Create toolbars for actions on files and items'''
        self.fileToolbar = self.addToolBar("File actions")
        self.fileToolbar.addAction(self.fileNewAction)
        self.fileToolbar.addAction(self.fileOpenAction)
        self.fileToolbar.addAction(self.fileSaveAction)
        self.fileToolbar.addAction(self.fileSaveAsAction)
        self.itemToolbar = self.addToolBar("Item actions")
        self.itemToolbar.addAction(self.undoAction)
        self.itemToolbar.addAction(self.redoAction)

#        self.itemToolBar.addAction(self.taskblockAddAction)
#        self.itemToolBar.addAction(self.taskAddAction)
#        self.itemToolBar.addAction(self.itemUpAction)
#        self.itemToolBar.addAction(self.itemDownAction)

    def closeEvent(self, event):
        '''If data has been changed, ask user if she wants to save it'''
        if not self.view.undoStack.isClean() and self.view.saveChangesDialog():
            self.view.fileSave()
        self.close()
    
    def createMenus(self):
        '''Create menu for actions on files'''
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.fileOpenAction)    
        self.fileMenu.addAction(self.fileNewAction)
        self.fileMenu.addAction(self.fileSaveAction)
        self.fileMenu.addAction(self.fileSaveAsAction)
        
    def createActions(self):
        '''Create all actions to be used in toolbars/menus: calls createAction()'''
        #File actions
        self.fileNewAction = self.createAction("&New", slot = self.newFile,
                shortcut = QtGui.QKeySequence.New, icon = "ebFileNew", tip = "New file",
                status = "Create a new file")
        self.fileOpenAction = self.createAction("&Open...", slot = self.fileOpen,
                shortcut = QtGui.QKeySequence.Open, icon = "ebFileOpen",tip = "Open file",
                status = "Open an existing earlybird tree")
        self.fileSaveAction = self.createAction("&Save", slot = self.fileSave,
                shortcut = QtGui.QKeySequence.Save, icon = "ebFileSave", tip = "Save file",
                status = "Save file")
        self.fileSaveAsAction = self.createAction("Save &As", slot = self.fileSaveAs,
                icon = "ebFileSaveAs", tip = "Save file as",
                status = "Save file as")
           
        #Item actions
        self.undoAction = self.createAction("Undo", slot = self.view.undoStack.undo,
               icon = "ebUndo", tip = "Undo",
               status = "Undo previous action in undo stack")    
        self.redoAction = self.createAction("Redo", slot = self.view.undoStack.redo,
               icon = "ebRedo", tip = "Redo",
               status = "Redo next action in undo stack")  
                
#        self.taskblockAddAction = self.createAction("Add block", slot = self.addTaskblock,
#               icon = "taskblockAdd", tip = "Add task block",
#               status = "Append task block to tree")
#
#        self.taskAddAction = self.createAction("Add task", slot = self.addTask,
#               icon = "taskAdd", tip = "Add top-level task",
#               status = "Append top-level task to tree")
#               
#        self.itemUpAction = self.createAction("Move up", slot = self.moveRowUp,
#               icon = "moveItemUp", tip = "Move up",
#               status = "Move selected item up in the tree")
#               
#        self.itemDownAction = self.createAction("Move down", slot = self.moveRowDown,
#           icon = "moveItemDown", tip = "Move down",
#           status = "Move selected item down in the tree")

    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, status = None):
        '''Function called to create each individual action'''
        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon("../images/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
        if status is not None:
            action.setStatusTip(status)
        if slot is not None:
            action.triggered.connect(slot)
        return action 
        
    def createStatusBar(self):                          
        self.status = self.statusBar()
        self.status.setSizeGripEnabled(False)
        self.status.showMessage("Ready")        
        
    def fileSaveAs(self):
        self.view.saveTodoDataAs()
        self.windowTitleSet()
        
    def fileSave(self):
        if self.view.filename:        
            self.view.saveTodoData()
        else:
            self.view.saveTodoDataAs()
            self.windowTitleSet()
        
    def fileOpen(self):
        '''Load earlybird file from memory.'''
        if self.view.loadEarlybirdFile():
            self.model = self.view.model  
            self.windowTitleSet()
            if self.view.filename:
                filenameNopath = QtCore.QFileInfo(self.view.filename).fileName()
                self.status.showMessage("Opened file: {0}".format(filenameNopath))
            
    def newFile(self):
        '''Opens new blank earlybird file'''
        self.view.newFile()
        self.windowTitleSet()
        
    def windowTitleSet(self):
        '''Displays filename as window title, if it exists.'''
        if self.view.filename:
            self.setWindowTitle("Earlybird - {}[*]".format(os.path.basename(self.view.filename)))
        else:
            self.setWindowTitle("Earlybird - <untitled>")
        
def main():
    #The following tells Windows to show icon in taskbar as well
    import ctypes
    myappid = u'earlyBird.todo.tree.0.1' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    ebApp = QtGui.QApplication(sys.argv)
    #print QtGui.QStyleFactory.keys()
    #ebApp.setStyle("Plastique")
    mainEb = EarlybirdMain(filename = None)#"simpleTodo.eb"
    mainEb.show()
    undoView = QtGui.QUndoView(mainEb.view.undoStack)
    undoView.show()
    sys.exit(ebApp.exec_())


if __name__ == "__main__":
    main()
    
    
#        def resizeWindowToTree(self):
#        #Based on: 
#        #http://stackoverflow.com/questions/26960006/in-qdialog-resize-window-to-contain-all-columns-of-qtableview     
#        margins = self.layout().contentsMargins()
#        marginWidth = margins.left() + margins.right()
#        frameWidth = self.treeView.frameWidth() * 2
#        vertHeaderWidth = 0 #self.treeView.verticalHeader().width()
#        horizHeaderWidth =self.treeView.header().length()
#        #print "horizHeaderWidth ", horizHeaderWidth
#        vertScrollWidth = self.treeView.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)  
#        newWidth = marginWidth + frameWidth + vertHeaderWidth + horizHeaderWidth + vertScrollWidth
#        if newWidth <= 800:
#            self.resize(newWidth, self.height())
#        else:
#            self.resize(800, self.height())  
    
#Below are the dregs.....perhaps one will become a Phoenix   
#
#    def itemChangedSlot(self, item):
#        '''Handles editing of task, comment'''
#        #print "item userdata:", item.data() #(role = QtCore.Qt.UserRole)
#        #print "Item changed name, row, col: ", item.text(), item.row(), item.column()
#        if item.column() == self.columnIndices["name"]:            
#            #print "checkbox state:", item.checkState()
#            itemUserData = item.data(role = QtCore.Qt.UserRole)
#            #print "itemChanged item.data(): ", itemUserData
#            if itemUserData["type"] == "taskblock":
#                print "blockhead"
#            elif itemUserData["type"] == "task":
#                print "Taskmaster"

#    def data(self, index, role):
#        if role == QtCore.Qt.BackgroundRole:
#            return QtGui.QBrush(QtGui.QColor(QtCore.Qt.green))       
#        return QtGui.QStandardItemModel.data(self, index, role)
            
#Following if you end up using QAbstractItemModel
#class TreeItem(object):
#    def __init__(self, data, parent):
#        self.parent = parent
#        self.itemData = data
#        self.childItems = []
#        if parent is not None:
#            parent.childItems.append(self)
