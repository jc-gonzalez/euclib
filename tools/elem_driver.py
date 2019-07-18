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

usage: python3 elem_driver.py [-h] -n NAME -i INF -I IN_FROM -o OUTF -O OUT_TO [-u]
                      [-t TIME_INTERVAL] [-c CYCLES] [-l LOG_FILE] [-d]

Script to be used as test driver to emulate an element

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Name of the emulated element
  -i INF, --in_folder INF
                        Folder to place the input products (can specify more
                        than one, see below)
  -I IN_FROM, --inputs_from IN_FROM
                        Folder to take the products that will be used as input
                        products
  -o OUTF, --out_folder OUTF
                        Folder to take the outputs from (can specify more than
                        one, see below)
  -O OUT_TO, --outputs_to OUT_TO
                        Folder where the outputs received will be stored
  -u, --user            Interactive mode: the user must press Enter at every
                        loop step
  -t TIME_INTERVAL, --time TIME_INTERVAL
                        Time interval between input product generations
  -c CYCLES, --cycles CYCLES
                        Number of cycles to provide a new product
  -l LOG_FILE, --log LOG_FILE
                        Name of the log file
  -d, --debug           Activated debug information

You can specify several input and output folders.  In addition, you
can specify an id for the kind of data flow that a given generated
input file belongs to.  Finally, you can specify an optional folder
that will be symbolically linked to the input/output folder.
The format is (both for -i and -o)

    -i <dataflow>:<folder>[:<folder-to-link>]

As an example, the following options:

    -i data:in.data:/mypath/in/data -i cmd:in.cmd:/mypath/in/cmd

will create the folders in.data and in.cmd, each of them being a
symbolic link to the folders /mypath/in/data and /mypath/in/cmd; the
generated files will use "data" and "cmd" and data flow identifiers.
The data flow id is mandatory, and the folder can be the same for
several data flow ids.
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

# noinspection PyUnresolvedReferences
from dirwatcher import define_dir_watcher

import argparse
import time
import queue
import shutil
import glob
import textwrap
import traceback

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
        """
        Initialize the class object
        :param name: Name for the emulated element
        :param inf: List of specified input folders
        :param outf: List of specified output folders
        :param infrom: Generated products are based on file in this folder
        :param outto: Store retrieved products in this folder
        :param interactive: True for an interactive operation
        :param cycles: Number of intervals for products generation
        :param interval: Length of time interval in seconds
        """
        self.name = name

        self.in_folder, self.infs = self.createIOFoldersGroup(inf)
        self.out_folder, self.outfs = self.createIOFoldersGroup(outf)
        self.inputs_from = infrom
        self.outputs_to = outto

        self.id = {cmd: 1 for cmd in self.in_folder.keys()}

        self.folders = self.infs + self.outfs + [infrom, outto]

        self.new_input_file = 0

        self.loopSleep = interval
        self.cycles = cycles
        self.isInteractive = interactive

        self.queues = []

        self.setupDirectories()

    @staticmethod
    def createIfNotExists(folder):
        """
        Create a nested folder if it does not exist
        :param folder: The folder to create
        """
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info('Creating folder {}'.format(folder))
            return True
        else:
            logger.info('Folder {} already exists'.format(folder))
            return False


    @staticmethod
    def createIOFoldersGroup(grp):
        """
        Splits folder specification provided by the user into group of
        folders for each data flow
        :param grp: the list of input/output folder specifications
        :return: The structure generated, and list of actual folders
        """
        dct = {}
        actual_folders = []
        for item in grp:
            items = item.split(':')
            if len(items) == 1:
                actual_folders.append(items[0])
                items.insert(0, 'data')
            if len(items) < 3:
                actual_folders.append(items[1])
                items.append(None)
            else:
                actual_folders.append(items[2])

            dct[items[0]] = [items[1], items[2]]

        return dct, actual_folders

    def setupDirectories(self):
        """
        Set up the different directories for operation
        :return:
        """
        for setOfFlds in [self.in_folder, self.out_folder]:
            for k, v in setOfFlds.items():
                actFld, lnkFld = (v[0], v[1])
                if lnkFld is None:
                    if not os.path.exists(actFld):
                        logger.warning('Folder {} does not exist!'.format(actFld))
                        self.createIfNotExists(actFld)
                    else:
                        logger.warning('Reusing existing folder {}'.format(actFld))
                else:
                    if not os.path.exists(lnkFld):
                        logger.error('Folder to link {} does not exist!'.format(lnkFld))
                        logger.error('Creating a new folder {}'.format(actFld))
                        self.createIfNotExists(actFld)
                    else:
                        if os.path.exists(actFld):
                            logger.warning('Renaming exiting folder {}!'.format(actFld))
                            os.rename(actFld, actFld + '.orig')
                        os.symlink(lnkFld, actFld)

        for fld in [self.inputs_from, self.outputs_to]:
            if not os.path.exists(fld):
                logger.warning('Folder {} does not exist!'.format(fld))
                self.createIfNotExists(fld)

        self.input_files = glob.glob(self.inputs_from + '/*')
        #pprint(self.input_files)

        for outf in self.outfs:
            q = queue.Queue()
            dwThr = define_dir_watcher(outf, q)
            self.queues.append( [q, dwThr, outf] )

    def monitor(self):
        """
        Check the queue for ouetput files (inputs to the emulated element)
        :return: True: continue operation, False: end
        """
        for qinfo in self.queues:
            q : queue.Queue = qinfo[0]
            #pprint(qinfo)
            #pprint(q)

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
        The files used get the following patterns substituted in theis names
        to generate the final file name:
        XXXXX - File id (0-filled)
        YYY - Flow group
        :return: -
        """
        for grp, n in self.id.items():
            pprint('{}: {}'.format(grp, n))
            obsid = '{:05d}'.format(n)
            ifile = self.input_files[self.new_input_file]
            new_file = ifile.replace('XXXXX', obsid).replace('YYY', grp)
            new_in_file = os.path.join(self.in_folder[grp][0], os.path.basename(new_file))
            pprint(new_in_file)
            shutil.copyfile(ifile, new_in_file + '.part')
            shutil.move(new_in_file + '.part', new_in_file)
            logger.debug('Product {} generated'.format(new_in_file))

            self.id[grp] = n + 1
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
            traceback.print_exc()

        self.terminate()

    def terminate(self):
        """
        Wrap-up and finish execution
        :return: -
        """
        for qinfo in self.queues:
            thr = qinfo[1]
            thr.join()
        logger.info('DONE')


def configureLogs(lvl, logfile='elem.log'):
    """
    Function to configure the output of the log system, to be used across the entire application.
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
    addInfo = """
        You can specify several input and output folders.  In addition, you
        can specify an id for the kind of data flow that a given generated
        input file belongs to.  Finally, you can specify an optional folder
        that will be symbolically linked to the input/output folder.
        The format is (both for -i and -o)

            -i <dataflow>:<folder>[:<folder-to-link>]

        As an example, the following options:

            -i data:in.data:/mypath/in/data -i cmd:in.cmd:/mypath/in/cmd

        will create the folders in.data and in.cmd, each of them being a
        symbolic link to the folders /mypath/in/data and /mypath/in/cmd; the
        generated files will use "data" and "cmd" and data flow identifiers.
        The data flow id is mandatory, and the folder can be the same for
        several data flow ids.
        """
    parser = argparse.ArgumentParser(description='Script to be used as test driver to emulate an element',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, #ArgumentDefaultsHelpFormatter,
                                     epilog=textwrap.dedent(addInfo))
    parser.add_argument('-n', '--name', dest='name', required=True,
                        help='Name of the emulated element')
    parser.add_argument('-i', '--in_folder', dest='inf', action='append', required=True,
                        help='Folder to place the input products (can specify more than one, see below)')
    parser.add_argument('-I', '--inputs_from', dest='in_from', required=True,
                        help='Folder to take the products that will be used as input products')
    parser.add_argument('-o', '--out_folder', dest='outf', action='append', required=True,
                        help='Folder to take the outputs from (can specify more than one, see below)')
    parser.add_argument('-O', '--outputs_to', dest='out_to', required=True,
                        help='Folder where the outputs received will be stored')
    parser.add_argument('-u', '--user', dest='interactive', action='store_true', default=False,
                        help='Interactive mode: the user must press Enter at every loop step')
    parser.add_argument('-t', '--time', dest='time_interval', type=float, default=5.0,
                        help='Time interval between input product generations')
    parser.add_argument('-c', '--cycles', dest='cycles', type=int, default=1,
                        help='Number of cycles to provide a new product')
    parser.add_argument('-l', '--log', dest='log_file', default='logfile',
                        help='Name of the log file')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
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
        logger.info("The period of products arrival checking will be " +
                    "{} seconds".format(args.time_interval))
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
