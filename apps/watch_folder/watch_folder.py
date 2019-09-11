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

from tools.dirwatcher import define_dir_watcher
from tools.actions import ActionsLauncher

import time
import argparse
import queue

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

LoopSleep = 1.0

rawQa = queue.Queue()
dwThrA = None
monitQueue = None
launcher = None

def configureLogs(lvl):
    """
    Function to configure the output of the log system, to be used across the
    entire application.
    :param lvl: Log level for the console log handler
    :return: -
    """
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('watchfolder.log')
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
    parser = argparse.ArgumentParser(description='Watches the folder where the script is ' +
                                                 'launched, and executed the actions ' +
                                                 'in the actions.json file in the same folder',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-D', '--dir', dest='directory', default='.',
                        help='Directory to monitor')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Activated debug information')

    return parser.parse_args()

def greetings():
    """
    Show log header
    :return: -
    """
    logger.info("==============================================================================")
    logger.info("watch_folder - Watch folder and execute actions on new file")
    logger.info("{}".format(__copyright__))
    logger.info("Last update {}".format(__date__))
    logger.info("Created by {} - {}".format(__author__, __email__))
    logger.info("==============================================================================")

def initialize(folder):
    """

    :return:
    """
    # Launch monitoring
    global rawQa, dwThrA, monitQueue, launcher
    rawQa = queue.Queue()
    dwThrA = define_dir_watcher(folder, rawQa)
    monitQueue = {'from': folder, 'to': '',
                  'this_folder_is': 'from',
                  'queue': rawQa, 'thread': dwThrA}
    launcher = ActionsLauncher('')

def monitor():
    """
    Check all the queues, looking for new entries, and launching the
    appropriate action (according to the actions object file
    :return: -
    """
    fromFolder = monitQueue['from']
    toFolder = monitQueue['to']
    thisFolder = monitQueue[monitQueue['this_folder_is']]
    q : queue.Queue = monitQueue['queue']
    while not q.empty():
        entry = q.get()
        bentry = os.path.basename(entry)
        if entry[-5:] == '.part' or \
            bentry == 'actions.json' or \
            bentry[0:4] == 'log.' or \
            bentry[0:4] == 'err.':
            continue
        logger.info('New file {}'.format(entry))

        logger.info('Launching...')
        launcher.launchActions(folder=thisFolder, file=entry,
                               src_dir=fromFolder, tgt_dir=toFolder)
        logger.info('done.')

def run(folder):
    """
    Launch the Controller process
    :return: -
    """

    # Create / List folders
    initialize(folder)

    # Run main loop
    runMainLoop()

    # When main loop is finished, wrap up and end program
    terminate()

def runMainLoop():
    """
    Run loop of Master
    :return: -
    """
    logger.info('START')
    iteration = 0

    try:
        while True:
            iteration = iteration + 1
            logger.debug('Iteration {}'.format(iteration))

            # Perform check of queues
            monitor()

            time.sleep(LoopSleep)

    except Exception as ee:
        logger.error('{}'.format(ee))
        logger.debug('Iteration {}'.format(iteration))

def terminate():
    """
    Wrap-up and finish execution
    :return: -
    """
    logger.info('END')
    dwThrA.join()

def main():
    """
    Main processor program
    """

    # Parse command line arguments
    args = getArgs()
    folder = args.directory

    # Set up homogeneous logging system
    configureLogs(logging.DEBUG if args.debug else logging.INFO)

    # Start message
    greetings()

    # Start time
    logger.info('Start!')
    time_start = time.time()

    # Launch process
    run(folder)

    # End time, closing
    time_end = time.time()
    logger.info('Done.')
    logger.info('Ellapsed time: {} s'.format(time_end - time_start))


if __name__ == '__main__':
    main()
