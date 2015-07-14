# -*- coding: utf-8 -*-
"""
earlybirdMain.py
     A wrapper for the EarlybirdTree class. It allows for user interaction
    with a to do tree that is defined in earlybirdTree.py.
    
Early bird to do tree. 
Because life ain't a list.
"""
import sys
import os
from PySide import QtGui, QtCore
from earlybirdTree import EarlybirdTree

class EarlybirdMain(QtGui.QMainWindow):
    '''
    Main window to wrap an EarlybirdTree
    '''
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
        self.fileToolbar.addAction(self.printFileAction)
        self.fileToolbar.addAction(self.fileNewAction)
        self.fileToolbar.addAction(self.fileOpenAction)
        self.fileToolbar.addAction(self.fileSaveAction)
        self.fileToolbar.addAction(self.fileSaveAsAction)
        self.itemToolbar = self.addToolBar("Item actions")
        self.itemToolbar.addAction(self.undoAction)
        self.itemToolbar.addAction(self.redoAction)
        self.itemToolbar.addAction(self.addTaskAction)
        self.itemToolbar.addAction(self.itemUpAction)
        self.itemToolbar.addAction(self.itemDownAction)

    def closeEvent(self, event):
        '''If data has been changed, ask user if she wants to save it'''
        if not self.view.undoStack.isClean():
            saveDialogResponse = self.view.saveChangesDialog()
            if saveDialogResponse == QtGui.QMessageBox.Cancel:
                event.ignore()
                return
            elif saveDialogResponse == QtGui.QMessageBox.Yes:
                self.view.saveTodoData()
        event.accept()
    
    def createMenus(self):
        '''Create menu for actions on files'''
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.printFileAction)
        self.fileMenu.addAction(self.fileOpenAction)    
        self.fileMenu.addAction(self.fileNewAction)
        self.fileMenu.addAction(self.fileSaveAction)
        self.fileMenu.addAction(self.fileSaveAsAction)
        
    def createActions(self):
        '''Create all actions to be used in toolbars/menus: calls createAction()'''
        #File actions
        self.printFileAction = self.createAction("&Print", slot = self.printFile,
                shortcut = QtGui.QKeySequence.Print, icon = "ebPrint", tip = "Print file",
                status = "Print file")
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
        self.addTaskAction = self.createAction("Add block", slot = self.addTask,
               icon = "ebAddTask", tip = "Add task",
               status = "Append top-level task to tree")
        self.itemUpAction = self.createAction("Move up", slot = self.moveRowUp,
               icon = "ebMoveUp", tip = "Move up",
               status = "Move selected item up in the tree")
        self.itemDownAction = self.createAction("Move down", slot = self.moveRowDown,
           icon = "ebMoveDown", tip = "Move down",
           status = "Move selected item down in the tree")

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
        
    def moveRowUp(self):
        selectedIndexes = self.view.selectedIndexes()
        self.view.moveRowUp(selectedIndexes[0])
        
    def moveRowDown(self):
        selectedIndexes = self.view.selectedIndexes()
        self.view.moveRowDown(selectedIndexes[0])
        
    def printFile(self):
        '''Saves the tree as PDF: it looks pretty ugly, so I look at this as
        a placeholder for a real print function: probably should just add
        this to save as, to save it as a pdf, as it really isn't printing at all!'''
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setPageSize(QtGui.QPrinter.Letter)
        printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
        printer.setOutputFileName("treeTest.pdf")
        painter = QtGui.QPainter()
        painter.begin(printer)
        painter.scale(20, 20)
        self.view.render(painter, QtCore.QPoint())
        painter.end()
        
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
        '''
        Load earlybird file from memory.
        '''
        if self.view.loadEarlybirdFile():
            self.model = self.view.model  
            self.windowTitleSet()
            if self.view.filename:
                filenameNopath = QtCore.QFileInfo(self.view.filename).fileName()
                self.status.showMessage("Opened file: {0}".format(filenameNopath))
            
    def newFile(self):
        '''
        Opens new blank earlybird file
        '''
        self.view.newFile()
        self.windowTitleSet()
        
    def addTask(self):
        self.view.addTask()
        
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
    ebApp.setStyle('Cleanlooks')  #cleanlooks
    #print QtGui.QStyleFactory.keys()
    #ebApp.setStyle("Plastique")
    mainEb = EarlybirdMain(filename = "../examples/simpleTree.eb")  #None
    mainEb.show()
    #undoView = QtGui.QUndoView(mainEb.view.undoStack)
    #undoView.show()
    sys.exit(ebApp.exec_())


if __name__ == "__main__":
    main()
    
    

    