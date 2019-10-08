#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watch_folder.py

usage: python3 watch_folder.py [-h] [-c CONFIG_FILE] [-d]

Watches the folder where the script is launched, and executed the actions
in the actions.json file in the same folder.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config CONFIG_FILE
                        Configuration file to use (default: None)
  -d, --debug           Activated debug information (default: False)

"""
#----------------------------------------------------------------------

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

_filedir_ = os.path.dirname(__file__)
_appsdir_, _ = os.path.split(_filedir_)
_basedir_, _ = os.path.split(_appsdir_)
sys.path.insert(0, os.path.abspath(os.path.join(_filedir_, _basedir_, _appsdir_)))

PYTHON2 = False
PY_NAME = "python3"
STRING = str

#----------------------------------------------------------------------

from tkinter import *
from appgui import App

import time
import argparse
import queue

from pprint import pprint

import logging
logger = logging.getLogger()

#----------------------------------------------------------------------

VERSION = '0.0.1'

__author__     = "J C Gonzalez"
__version__    = VERSION
__license__    = "LGPL 3.0"
__status__     = "Development"
__copyright__  = "Copyright (C) 2015-2019 by Euclid SOC Team @ ESAC / ESA"
__email__      = "jcgonzalez@sciops.esa.int"
__date__       = "June 2019"
__maintainer__ = "J C Gonzalez"
#__url__       = ""

#----------------------------------------------------------------------

LoopSleep = 1.0

rawQa = queue.Queue()
dwThrA = None
monitQueue = None
launcher = None

def configureLogs(lvl, logfile):
    """
    Function to configure the output of the log system, to be used across the
    entire application.
    :param lvl: Log level for the console log handler
    :return: -
    """
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(logfile)
    c_handler.setLevel(lvl)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s %(levelname).1s %(name)s %(module)s:%(lineno)d %(message)s',
                                 datefmt='%y-%m-%d %H:%M:%S')
    f_format = logging.Formatter('{asctime} {levelname:4s} {name:s} {module:s}:{lineno:d} {message}',
                                 style='{')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    lmodules = os.getenv('LOGGING_MODULES', default='').split(':')
    for lname in reversed(lmodules):
        lgr = logging.getLogger(lname)
        if not lgr.handlers:
            lgr.addHandler(c_handler)
            lgr.addHandler(f_handler)
        # logger.debug('Configuring logger with id "{}"'.format(lname))

def getArgs():
    """
    Parse arguments from command line

    :return: args structure
    """
    parser = argparse.ArgumentParser(description='Simulates the I/O operations of an element, ' +
                                                 'and shows the log messages',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-e', '--element', dest='element', default='MOC',
<<<<<<< HEAD
                        help='Element Acronym')
    parser.add_argument('-f', '--files_dir', dest='data_dir', default='./data',
                        help='Directory where the data files to be sent are located')
    parser.add_argument('-o', '--outgoing', dest='outgoing_dirs', default='SIS:./out',
                        help='Comma separated of pairs ELEM:DIR, that indicates the folder DIR' +
			'where data must be stored to be sent to element ELEM')
    parser.add_argument('-i', '--incoming', dest='incoming_dir', default='./in',
                        help='Directory where remote files are received')
    parser.add_argument('-l', '--log', dest='logfile', default='simelem.log',
                        help='Log info file name')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Activate debug information')
=======
                        help='Directory where the element simulator is deployed')
    parser.add_argument('-D', '--dir', dest='directory', default='.',
                        help='Directory where the element simulator is deployed')
    parser.add_argument('-l', '--log', dest='logfile', default='simelem.log',
                        help='Directory to monitor')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Activated debug information')
>>>>>>> e3046e850723a98350d75a1cb74de86e1b407462

    return parser.parse_args()

def greetings():
    """
    Show log header
    :return: -
    """
    logger.info("==============================================================================")
    logger.info("simelem - Simulates the I/O operations of an element")
    logger.info("{}".format(__copyright__))
    logger.info("Last update {}".format(__date__))
    logger.info("Created by {} - {}".format(__author__, __email__))
    logger.info("==============================================================================")


def main():
    """
    Main processor program
    """
    args = getArgs()
    configureLogs(logging.DEBUG if args.debug else logging.INFO,
                  args.logfile)

    root = Tk()
<<<<<<< HEAD
    app = App(parent=root, args=args, logger=logger)
=======
    app = App(parent=root, args=args)
>>>>>>> e3046e850723a98350d75a1cb74de86e1b407462
    root.mainloop()
    return


if __name__ == '__main__':
    main()
