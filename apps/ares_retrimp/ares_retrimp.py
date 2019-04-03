#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
ares_retrimp

Ares Retrieve-Import Tool with GUI
'''

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '../..')))

from tkinter import *

PYTHON2 = False
PY_NAME = "python3"
STRING = str

from appgui import App

# details
__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = "0.0.2"
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""


def main():
    root = Tk()
    app = App(parent=root)
    root.mainloop()


if __name__ == '__main__':
    main()
