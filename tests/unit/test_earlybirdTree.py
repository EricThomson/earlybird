# -*- coding: utf-8 -*-
"""
test_earlybirdTree.py
Basic unit testing for earlybirdTree.py, in particular loading files.
Make sure the folder containing the earlybird folder is in your path.
"""
import sys
import unittest
from PySide import QtGui
from earlybird.scripts.earlybirdTree import EarlybirdTree

  
class Test_EarlybirdTree(unittest.TestCase):
    '''Test the earlybirdtree class'''
    def setUp(self):
        #try/except is in case qapplication instance already exists
        #http://lists.qt-project.org/pipermail/pyside/2013-October/001670.html
        try: 
            self.ebApp = QtGui.QApplication(sys.argv)
        except:
            pass
        self.tree = EarlybirdTree()
       
    def test_load_improperly_formatted_file_returns_false(self):
        self.assertEqual(self.tree.loadEarlybirdFile(filename = "improperFormatTest.eb"),
                         False)
        
    def test_load_properly_formatted_file_returns_true(self):
        self.assertEqual(self.tree.loadEarlybirdFile(filename = "properFormatTest.eb"),
                         True)
        
    
def main():
    unittest.main(buffer = True)
    
if __name__ == "__main__":
    main()
    

