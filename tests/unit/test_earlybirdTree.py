# -*- coding: utf-8 -*-
"""
test_earlybirdTree.py
Basic unit testing for earlybirdTree.py, in particular loading files.
"""
import sys
import unittest
from PySide import QtGui
from earlybird.scripts.earlybirdTree import EarlybirdTree

  
class Test_EarlybirdTree(unittest.TestCase):
    '''Test the game'''
    def setUp(self):
        #try/except is in case qapplication intance already exists
        #http://lists.qt-project.org/pipermail/pyside/2013-October/001670.html
        try: 
            self.ebApp = QtGui.QApplication(sys.argv)
        except:
            pass
        self.tree = EarlybirdTree()
       
    def test_load_pure_top_block_tree_returns_true(self):
        self.assertEqual(self.tree.loadEarlybirdFile(filename = "blockOnlyTest.eb"),
                         True)

    def test_load_pure_top_task_tree_returns_false(self):
        self.assertEqual(self.tree.loadEarlybirdFile(filename = "taskOnlyTest.eb"),
                         False)
        
    def test_load_mixed_tree_returns_true(self):
        self.assertEqual(self.tree.loadEarlybirdFile(filename = "mixedTest.eb"),
                         True)
        
    
def main():
    unittest.main(buffer = True)
    
if __name__ == "__main__":
    main()
    

