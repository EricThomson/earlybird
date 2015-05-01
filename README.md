#Earlybird To Do Tree
A simple to-do tree desktop application written in PySide. I effectively took what I was already doing extremely inefficiently in Word, and ported it to Python. 

Displaying a to do tree involves two main classes:
- `EarlybirdTree`: the core tree view. It contains the data model as well as basic methods for operations on the tree (loading and saving files, adding edited items to the undo stack, etc.). This is defined in `earlybirdTree.py`.
- `EarlybirdMain`: a simple main window wrapper for `EarlybirdTree` objects. It allows the user to interact with the tree's methods using menus and toolbars. This class is defined in `earlybirdMain.py`.

The data for a tree is stored in a json file with an `.eb` suffix. The folder `earlybird/examples` includes the following examples:
- `simpleTree.eb`   A small to-do tree. Run `earlybirdMain.py` and load it.


###To do
- Add item 
- Remove item 
- Move item up
- Move item down
- Daily schedule
