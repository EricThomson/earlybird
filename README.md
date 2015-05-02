#Earlybird To Do Tree
A simple to-do tree desktop application written in PySide. I effectively took what I was already doing extremely inefficiently in Word, and ported it to Python. 

The to do tree involves two main classes:
- `EarlybirdTree` (defined in `earlybirdTree.py`): the core tree view. It contains the data model as well as basic methods for operations on the tree (loading and saving files, adding edited items to the undo stack, etc.). 
- `EarlybirdMain` (defined in `earlybirdMain.py`): a simple main window wrapper for `EarlybirdTree` objects. It allows the user to interact with the tree's methods using menus and toolbars. 

The data for a tree is stored in a json file with an `.eb` suffix. The folder `earlybird/examples` includes the following examples:
- `simpleTree.eb`   A small to-do tree. Run `earlybirdMain.py` and load it.


###To do
- Add item 
- Remove item 
- Move item up
- Move item down
- Daily schedule

####Open questions

*setData versus undoStack push*

There seems to be redundancy between our reimplementation of `setData` (in `StandardItem`) and the undo stack. In the StandardItem subclass of QStandardItem, for instance in checkbox, we have: 

    QtGui.QStandardItem.setData(self, newValue, role) 
    
But on the other hand, it is supposed to be sufficient to simply push a change onto the undo stack, and that is what makes the change, for instance in itemDataChangedSlot:

    checkStateChangeCommand=CommandCheckStateChange(self, item, oldValue, newValue)
    self.undoStack.push(checkStateChangeCommand)
    
Simply pushing that command onto the undo stack is supposed to be sufficient to get things to work, so setting in within setData seems redundant. But if I remove the setData call above, the checkboxes don't even show up, much less change values correctly. 