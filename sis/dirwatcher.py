#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dirwatcher.py

Classes to monitor the changes in one or more directories.
It uses watchdog package.

Sample command line:
$ python3 ./dirwatcher.py
"""
#----------------------------------------------------------------------

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

import os, sys
_filedir_ = os.path.dirname(__file__)
_appsdir_, _ = os.path.split(_filedir_)
_basedir_, _ = os.path.split(_appsdir_)
sys.path.insert(0, os.path.abspath(os.path.join(_filedir_, _basedir_, _appsdir_)))

PYTHON2 = False
PY_NAME = "python3"
STRING = str

#----------------------------------------------------------------------

import threading
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import logging
logger = logging.getLogger()

#----------------------------------------------------------------------

VERSION = '0.0.1'

__author__     = "J C Gonzalez"
__version__    = VERSION
__license__    = "LGPL 3.0"
__status__     = "Development"
__copyright__  = "Copyright 2015-2019, J C Gonzalez"
__email__      = "jcgonzalez@sciops.esa.int"
__maintainer__ = "J C Gonzalez"
#__url__       = ""

#----------------------------------------------------------------------

def define_dir_watcher(path, file_queue):
    """
    Function to define and launch a directory watcher
    :param path: the folder path
    :param file_queue: list where the appearing filename will be stored
    :return: the thrID
    """
    dwThr = threading.Thread(target=run_dir_watcher, args=(path, file_queue,))
    dwThr.start()
    logger.info('Dir.Watcher created, monitoring path {}'.format(path))
    return dwThr

def run_dir_watcher(path, alist):
    """
    Function executed in a thread to monitor a single path folder
    :param path:
    :param alist:
    :return:
    """
    w = Watcher(path=path, file_queue=alist)
    w.run()
    logger.debug('Thread monitoring path {}'.format(path))

class Watcher:
    """
    Simple class to monitor (with watchdog) the events in a given folder
    """
    def __init__(self, path, file_queue):
        self.observer = Observer(timeout=0.9)
        self.observer.event_queue.maxsize = 100
        self.folder = path
        self.evt_handler = Handler(file_queue)

    def run(self):
        """
        Launches the execution of the Watcher
        """
        self.observer.schedule(self.evt_handler, self.folder) #, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            logger.error("Error in dir. watcher for path {}".format(self.folder))

        self.observer.join()

class Handler(FileSystemEventHandler):
    """
    Simple events handler, stores in provided list the file names for
    the monitored events
    """
    def __init__(self, file_queue):
        super(Handler, self).__init__()
        self.file_queue = file_queue

    def on_any_event(self, event):
        """

        :param event:
        :return:
        """
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            pth = event.src_path
            if not pth.endswith('.part'):  # to handle files too big
                self.file_queue.put(pth)
                logger.debug('Adding {} to list {}'.format(pth, self.file_queue))

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            pth = event.src_path
            if not pth.endswith('.part'): # to handle files too big
                self.file_queue.put(pth)
                logger.debug('Adding {} to list {}'.format(pth, self.file_queue))

        return None


if __name__ == '__main__':
    pass
