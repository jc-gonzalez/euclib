#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watch_folder.py

usage: watch_folder.py [-h] [-D DIRECTORY] [-R REMOTE_DIRECTORY] [-l LOGFILE]
                       [-d]

Watches the folder where the script is launched, and executed the actions in
the actions.json file in the same folder

optional arguments:
  -h, --help            show this help message and exit
  -D DIRECTORY, --dir DIRECTORY
                        Directory to monitor (default: .)
  -R REMOTE_DIRECTORY, --remote REMOTE_DIRECTORY
                        Directory to monitor in remote machine, expected
                        format is USER@HOST:DIR (default: None)
  -l LOGFILE, --log LOGFILE
                        Directory to monitor (default: watchfolder.log)
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
import subprocess

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

def configureLogs(lvl, logfile, console):
    """
    Function to configure the output of the log system, to be used across the
    entire application.
    :param lvl: Log level for the console log handler
    :param logfile: Name of the log file
    :return: -
    """
    logger.setLevel(lvl)

    # Create handler and formatters, add formatter to handler,
    #  and add handler to the logger
    f_handler = logging.FileHandler(logfile)
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('{asctime} {levelname:4s} {name:s} {module:s}:{lineno:d} {message}',
                                 style='{')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)

    if console:
        c_handler = logging.StreamHandler()
        c_handler.setLevel(lvl)
        c_format = logging.Formatter('%(asctime)s %(levelname).1s %(name)s %(module)s:%(lineno)d %(message)s',
                                     datefmt='%y-%m-%d %H:%M:%S')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

    # Add handlers to the logger
    lmodules = os.getenv('LOGGING_MODULES', '').split(':')
    for lname in reversed(lmodules):
        lgr = logging.getLogger(lname)
        if not lgr.handlers:
            lgr.addHandler(f_handler)
            if console: lgr.addHandler(c_handler)
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
    parser.add_argument('-R', '--remote', dest='remote_directory', default=None,
                        help='Directory to monitor in remote machine, expected format is USER@HOST:DIR')
    parser.add_argument('-l', '--log', dest='logfile', default='watchfolder.log',
                        help='Directory to monitor')
    parser.add_argument('-c', '--console', dest='console', action='store_true', default=False,
                        help='Show log in console')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
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

def initialize(folder, remote=None):
    """
    Initialize directory (andn remote folder) watcher object
    :return:
    """
    # Launch monitoring
    global rawQa, dwThrA, monitQueue, launcher
    isRemote = remote is not None
    remoteAddr, remoteFolder = '', ''
    if isRemote:
        items = remote.split(':')
        remoteAddr, remoteFolder = items[0], items[1]
    rawQa = queue.Queue()
    dwThrA = define_dir_watcher(folder, rawQa)
    monitQueue = {'from': folder, 'to': '',
                  'this_folder_is': 'from',
                  'is_remote': isRemote,
                  'address': remoteAddr,
                  'remote_folder': remoteFolder,
                  'current_items': None,
                  'queue': rawQa, 'thread': dwThrA}
    launcher = ActionsLauncher('')

def getRemoteFolderItems(folder, address):
    """
    Get the list of files in a remote folder
    :param folder: Remote folder to check
    :param address: Address (user@host) to connect to the remote host
    :return: List of files
    """
    cmd = 'ls -1 {}'.format(folder)
    ssh = subprocess.Popen(['ssh', address, cmd],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    #if result == []:
    #    error = ssh.stderr.readlines()
    #    print('ERROR: %s' % error)
    return result

def computeDiffs(lst1, lst2):
    ldiff = []
    for l in lst2:
        if l not in lst1:
            ldiff.append(l.decode('ascii'))
    return ldiff

def skipControlFiles(entry):
    """
    Return true if the file can be skipped
    :param entry: The file name
    :return: True/False
    """
    bentry = os.path.basename(entry)
    if entry[-5:] == '.part' or \
            bentry == 'actions.json' or \
            bentry[0:4] == 'log.' or \
            bentry[0:4] == 'err.':
        return True
    return False

def synchronizeRemoteAndLocalFolders(mqueue):
    """
    Check remote folder, and get new items found into local folder 
    :param mqueue: Paramters for local and remote folders monitoring
    :return: -
    """
    localDir = mqueue['from']
    isRemote = mqueue['is_remote']
    if isRemote:
        address, remoteDir = mqueue['address'], mqueue['remote_folder']
        current_items = mqueue['current_items']
        if current_items is None:
            current_items = getRemoteFolderItems(remoteDir, address)
        new_items_list = getRemoteFolderItems(remoteDir, address)
        new_items = computeDiffs(current_items, new_items_list)
        for item in new_items:
            if skipControlFiles(item): continue
            cmd = 'scp -qC {}:{}/{} {}/'.format(address, remoteDir, item, localDir)
            subprocess.call(cmd.split())

        mqueue['current_items'] = new_items_list

def monitor():
    """
    Check all the queues, looking for new entries, and launching the
    appropriate action (according to the actions object file
    :return: -
    """
    # Get remote new entries into local folder
    global monitQueue
    synchronizeRemoteAndLocalFolders(monitQueue)

    # Evaluate new events
    fromFolder = monitQueue['from']
    toFolder = monitQueue['to']
    thisFolder = monitQueue[monitQueue['this_folder_is']]
    q : queue.Queue = monitQueue['queue']
    while not q.empty():
        entry = q.get()
        if skipControlFiles(entry): continue
        logger.info('New file {}'.format(entry))
        logger.info('Launching...')
        launcher.launchActions(folder=thisFolder, file=entry,
                               src_dir=fromFolder, tgt_dir=toFolder)
        logger.info('done.')

def run(folder, remote=None):
    """
    Launch the Controller process
    :return: -
    """

    # Create / List folders
    initialize(folder, remote)

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
    remote = args.remote_directory

    # Set up homogeneous logging system
    configureLogs(lvl=logging.DEBUG if args.debug else logging.INFO,
                  logfile=args.logfile,
                  console=args.console)

    # Start message
    greetings()

    # Start time
    logger.info('Start!')
    time_start = time.time()

    # Launch process
    run(folder, remote)

    # End time, closing
    time_end = time.time()
    logger.info('Done.')
    logger.info('Ellapsed time: {} s'.format(time_end - time_start))


if __name__ == '__main__':
    main()
