#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
elem_driver.py

Driver to emulate the operation of an element, placing products in
a provided IN folder, and retrieving products from an OUT folder
(both IN and OUT operations, from the perspective of the system
that interfaces with the emulated element).

The placement of product in the IN folder can be either periodic,
or interactive (upon signal from the user).

usage: python3 elem_driver.py [-h]
                      -n NAME -i INF -I IN_FROM -o OUTF -O OUT_TO
                      [-u] [-t TIME_INTERVAL] [-d]

Script to be used as test driver to emulate an element

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Name of the emulated element (default: None)
  -i INF, --in_folder INF
                        Folder to place the input products (default: None)
  -I IN_FROM, --inputs_from IN_FROM
                        Folder to take the products that will be used as input
                        products (default: None)
  -o OUTF, --out_folder OUTF
                        Folder to take the outputs from (default: None)
  -O OUT_TO, --outputs_to OUT_TO
                        Folder where the outputs received will be stored
                        (default: None)
  -u, --user            Interactive mode: the user must press Enter at every
                        loop step (default: False)
  -t TIME_INTERVAL, --time TIME_INTERVAL
                        Time interval between input product generations
                        (default: None)
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

from dirwatcher import define_dir_watcher

import argparse
import time
import queue
import shutil
import glob

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
__date__       = "July 2019"
__maintainer__ = "J C Gonzalez"
#__url__       = ""

#----------------------------------------------------------------------

class EmulElem:
    """
    Class EmulElem

    Implements methods to elumate the provision of products from an element, and
    the retrieval of products to be consumed by the same element
    """

    def __init__(self, name, inf, outf, infrom, outto,
                 interactive=False, cycles=1, interval=3.):
        self.name = name
        self.in_folder = inf
        self.inputs_from = infrom
        self.out_folder = outf
        self.outputs_to = outto

        self.input_files = glob.glob(infrom + '/*')
        self.new_input_file = 0
        self.id = 1

        self.loopSleep = interval
        self.cycles = cycles
        self.isInteractive = interactive

        # Ensure folders exist before launching the operation
        for fld in [inf, outf, infrom, outto]:
            if not os.path.exists(fld):
               logger.error('ERROR: Folder {} does not exist!'.format(fld))

        self.outQ = queue.Queue()
        self.outDwThr = define_dir_watcher(outf, self.outQ)
        self.queues = [self.outQ]

    def monitor(self):
        """
        Check the queue for output files (inputs to the emulated element)
        :return: True: continue operation, False: end
        """
        for qq in self.queues:
            q : queue.Queue = qq
            while not q.empty():
                entry = q.get()
                if entry[-5:] == '.part': continue

                bentry = os.path.basename(entry)
                if bentry == "QUIT": return False

                # New file in out folder
                logger.info('New file to be processed: {}'.format(entry))

                # Archive in the out repository
                newFile = os.path.join(self.outputs_to, bentry)
                shutil.move(entry, newFile)
                logger.info('File stored in internal {} repository'.format(self.name))

        return True

    def generateNewProduct(self):
        """
        Create new file, and put it in the IN folder (pushed from the element)
        :return: -
        """
        id = '{:05d}'.format(self.id)
        ifile = self.input_files[self.new_input_file]
        new_file = ifile.replace('XXXXX', id)
        new_in_file = os.path.join(self.in_folder, os.path.basename(new_file))

        shutil.copyfile(ifile, new_in_file + '.part')
        shutil.move(new_in_file + '.part', new_in_file)
        logger.debug('Product {} generated'.format(new_in_file))

        self.id = self.id + 1
        self.new_input_file = (self.new_input_file + 1) % len(self.input_files)

    def run(self):
        """
        Launch the element
        :return: -
        """
        logger.info('START')
        iteration = 0

        try:
            while True:
                iteration = iteration + 1
                logger.debug('Iteration {}'.format(iteration))

                if self.isInteractive:
                    input("Press Enter to continue...")
                else:
                    time.sleep(self.loopSleep)

                # Monitor OUT folder (inputs for the element)
                if not self.monitor(): break

                # Provide new file to the IN folder (outputs from the element)
                if (iteration % self.cycles) == 0:
                    self.generateNewProduct()

        except Exception as ee:
            logger.error('{}'.format(ee))
            logger.debug('Iteration {}'.format(iteration))

        self.terminate()

    def terminate(self):
        """
        Wrap-up and finish execution
        :return: -
        """
        logger.info('DONE')
        self.outDwThr.join()


def configureLogs(lvl, logfile='elem.log'):
    """
    Function to configure the output of the log system, to be used across the entire application.
    :return: -
    """
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('logfile')
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

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    lmodules = os.getenv('LOGGING_MODULES','').split(':')
    for lname in reversed(lmodules):
        lgr = logging.getLogger(lname)
        if not lgr.handlers:
            lgr.addHandler(c_handler)
            lgr.addHandler(f_handler)
        logger.debug('Configuring logger with id "{}"'.format(lname))

def getArgs():
    """
    Parse arguments from command line

    :return: args structure
    """
    parser = argparse.ArgumentParser(description='Script to be used as test driver to emulate an element',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--name', dest='name', required=True,
                        help='Name of the emulated element')
    parser.add_argument('-i', '--in_folder', dest='inf', required=True,
                        help='Folder to place the input products')
    parser.add_argument('-I', '--inputs_from', dest='in_from', required=True,
                        help='Folder to take the products that will be used as input products')
    parser.add_argument('-o', '--out_folder', dest='outf', required=True,
                        help='Folder to take the outputs from')
    parser.add_argument('-O', '--outputs_to', dest='out_to', required=True,
                        help='Folder where the outputs received will be stored')
    parser.add_argument('-u', '--user', dest='interactive', action='store_true',
                        help='Interactive mode: the user must press Enter at every loop step')
    parser.add_argument('-t', '--time', dest='time_interval',
                        help='Time interval between input product generations')
    parser.add_argument('-c', '--cycles', dest='cycles',
                        help='Number of cycles to provide a new product')
    parser.add_argument('-l', '--log', dest='log_file', default='logfile',
                        help='Name of the log file')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Activated debug information')
    return parser.parse_args()

def greetings(args):
    """
    Show log header
    :return: -
    """
    logger.info("==============================================================================")
    logger.info("{} Emulation Driver".format(args.name))
    logger.info("{}".format(__copyright__))
    logger.info("Last update {}".format(__date__))
    logger.info("Created by {} - {}".format(__author__, __email__))
    logger.info("------------------------------------------------------------------------------")
    logger.info("{} Internal storage has the following areas:".format(args.name))
    logger.info("  - Products data source: {}".format(args.in_from))
    logger.info("  - Retrieved products repository: {}".format(args.out_to))
    logger.info("Interface folders are:")
    logger.info("  - {}  ==> {}".format(args.name, args.inf))
    logger.info("  - {}  <== {}".format(args.name, args.outf))
    if args.interactive:
        logger.info("Running in INTERACTIVE mode")
    else:
        logger.info("The period of products arrival checking will be {} seconds".format(args.time_interval))
    logger.info("A new product will be generated every {} cycles".format(args.cycles))
    logger.info("==============================================================================")


def main():
    """
    Main processor program
    """

    # Parse command line arguments
    args = getArgs()

    # Set up homogeneous logging system
    configureLogs(logging.DEBUG if args.debug else logging.INFO,
                  args.log_file)

    # Start message
    greetings(args)

    # Start time
    logger.info('Start!')
    time_start = time.time()

    # Create and launch controller
    ctrl = EmulElem(name=args.name,
                    inf=args.inf, outf=args.outf,
                    infrom=args.in_from, outto=args.out_to,
                    interactive=args.interactive,
                    cycles=int(args.cycles),
                    interval=float(args.time_interval))
    ctrl.run()

    # End time, closing
    time_end = time.time()
    logger.info('Done.')
    logger.info('Ellapsed time: {} s'.format(time_end - time_start))


if __name__ == '__main__':
    main()
