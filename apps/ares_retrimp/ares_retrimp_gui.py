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
_filedir_ = os.path.dirname(__file__)
_appsdir_, _ = os.path.split(_filedir_)
_basedir_, _ = os.path.split(_appsdir_)
sys.path.insert(0, os.path.abspath(os.path.join(_filedir_, _basedir_, _appsdir_)))

from tkinter import *

PYTHON2 = False
PY_NAME = "python3"
STRING = str

from appgui import App

import logging
logger = logging.getLogger()


VERSION = '0.0.2'

__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = VERSION
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""


def configureLogs():
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    #c_format = logging.Formatter('%(asctime)s %(levelname).1s %(name)s %(module)s:%(lineno)d %(message)s',
    #                             datefmt='%y-%m-%d %H:%M:%S')
    c_format = logging.Formatter('%(asctime)s %(levelname).1s %(module)s:%(lineno)d %(message)s')
    c_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    for lname in os.environ['LOGGING_MODULES'].split(':'):
        lgr = logging.getLogger(lname)
        if not lgr.handlers: lgr.addHandler(c_handler)


def main():
    configureLogs()
    root = Tk()
    app = App(parent=root)
    root.mainloop()


if __name__ == '__main__':
    main()
