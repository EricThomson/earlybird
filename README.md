# Earlybird To Do Tree
A simple to-do tree application written in PySide.

The application includes two main classes:
- `EarlybirdTree` (defined in `earlybirdTree.py`): the core tree view. It contains the data model as well as basic methods for operations on the tree (loading and saving files, adding edited items to the undo stack, etc.). 
- `EarlybirdMain` (defined in `earlybirdMain.py`): a simple main window wrapper for `EarlybirdTree` objects. It allows the user to more conveniently interact with the tree's methods using menus and toolbars. 

The data for a tree is stored in a json file with an `.eb` extension. The eb files contain an array of tasks, each task consists of the `name` of the task (e.g., "Clean room"), and the `done` state of the task (e.g., `true`). Each task can also contain a nested array of tasks.

## Getting started
I recommend starting by running `earlybirdMain`. The folder `earlybird/examples` includes the following example, which you can load: 

- `simpleTree.eb`   

Using the app should be intuitive once you have the example loaded.

### Conventions for variable names
- Task-related variables: taskRow/ newTaskRow ; taskNameItem / newTaskNameItem
- Children and parents: parentIndex/parentItem ; childIndex/childItem; itemIndex/item
    
#### Open questions

*setData versus undoStack push*

There seems to be redundancy between our reimplementation of `setData` (in `StandardItem`) and the undo stack. In the StandardItem subclass of QStandardItem, for instance in checkbox, we have: 

    QtGui.QStandardItem.setData(self, newValue, role) 
    
But on the other hand, it is supposed to be sufficient to simply push a change onto the undo stack, and that is what makes the change, for instance in itemDataChangedSlot:

    checkStateChangeCommand=CommandCheckStateChange(self, item, oldValue, newValue)
    self.undoStack.push(checkStateChangeCommand)
    
Simply pushing that command onto the undo stack is supposed to be sufficient to get things to work, so setting it within setData seems redundant. But if I remove the setData call above, the checkboxes don't even show up, much less change values correctly. 
