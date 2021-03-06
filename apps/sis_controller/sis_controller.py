#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sis_controller.py

usage: sis_controller.py [-h] [-c CONFIG_FILE] [-b BASE_PATH] [-d] [-r]

Script to be used as proof of concept for SIS data circulation

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config CONFIG_FILE
                        Configuration file to use (default: None)
  -b BASE_PATH, --base BASE_PATH
                        Base path, overwrites the path specified in the
                        config. file (default: None)
  -d, --debug           Activated debug information (default: False)
  -r, --reuse_folders   Reuse existing folders, avoid overwriting them
                        (default: False)
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

from sis.controller import Controller

import time
import argparse

#from pprint import pprint

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
    lmodules = os.environ['LOGGING_MODULES'].split(':')
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
    parser = argparse.ArgumentParser(description='Script to be used as proof of concept for SIS data circulation',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config', dest='config_file',
                        help='Configuration file to use')
    parser.add_argument('-b', '--base', dest='base_path',
                        help='Base path, overwrites the path specified in the config. file')
    parser.add_argument('-l', '--log', dest='logfile', default='sis.log',
                        help='Directory to monitor')
    parser.add_argument('-r', '--reuse_folders', dest='reuse_folders', action='store_true',
                        help='Reuse existing folders, avoid overwriting them')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Activated debug information')

    return parser.parse_args()

def greetings():
    """
    Show log header
    :return: -
    """
    logger.info("==============================================================================")
    logger.info("SIS-Controller - SIS data circulation controller")
    logger.info("{}".format(__copyright__))
    logger.info("Last update {}".format(__date__))
    logger.info("Created by {} - {}".format(__author__, __email__))
    logger.info("==============================================================================")


def main():
    """
    Main processor program
    """

    # Parse command line arguments
    args = getArgs()
    recreate_folders = not args.reuse_folders

    # Set up homogeneous logging system
    configureLogs(lvl=logging.DEBUG if args.debug else logging.INFO,
                  logfile=args.logfile)

    # Start message
    greetings()

    # Start time
    logger.info('Start!')
    time_start = time.time()

    # Create and launch controller
    ctrl = Controller(cfg_file=args.config_file,
                      create_folders=recreate_folders,
                      base_path=args.base_path if args.base_path else None)
    ctrl.run()

    # End time, closing
    time_end = time.time()
    logger.info('Done.')
    logger.info('Ellapsed time: {} s'.format(time_end - time_start))


if __name__ == '__main__':
    main()
