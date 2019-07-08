#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oss_enhancer.py

Starting module for OSS_Extractor application.

usage: oss_enhancer.py [-h] [-o OSS_FILE] [-f FITS_FILE] [-O OBS_ID] [-d]

Script to be used to append OSS Obs.Id. info to FITS file

optional arguments:
  -h, --help            show this help message and exit
  -o OSS_FILE, --oss OSS_FILE
                        OSS XML file to use (default: None)
  -f FITS_FILE, --fits FITS_FILE
                        FITS file to append the Obs.Id. info table (default:
                        None)
  -O OBS_ID, --obsid OBS_ID
                        Observation Id. (default: None)
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

from ess.oss_reader import OSS

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

def configureLogs(lvl):
    """
    Function to configure the output of the log system, to be used across the entire application.
    :return: -
    """
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('sis.log')
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
    parser = argparse.ArgumentParser(description='Script to be used to append OSS Obs.Id. info to FITS file',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--oss', dest='oss_file',
                        help='OSS XML file to use')
    parser.add_argument('-f', '--fits', dest='fits_file',
                        help='FITS file to append the Obs.Id. info table')
    parser.add_argument('-O', '--obsid', dest='obs_id',
                        help='Observation Id.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Activated debug information')
    return parser.parse_args()

def greetings():
    """
    Show log header
    :return: -
    """
    logger.info("==============================================================================")
    logger.info("OSS-Enhancer - OSS Obs. Id. information appender to FITS file")
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

    # Set up homogeneous logging system
    configureLogs(logging.DEBUG if args.debug else logging.INFO)

    # Start message
    greetings()

    # Start time
    logger.info('Start!')
    time_start = time.time()

    # Create OSS object
    oss = OSS(args.oss_file)
    logger.info(f'New OSS object created from {args.oss_file}')

    # Add info table to FITS file
    if oss.addObsDataToFits(file=args.fits_file, obsid=args.obs_id):
        logger.info(f'New table with obs. id. {args.obs_id} ' + \
                    f'info appended to FITS file {args.fits_file}')
    else:
        logger.warning('Could not add new obs.id. info table to file')

    # End time, closing
    time_end = time.time()
    logger.info('Done.')
    logger.info('Ellapsed time: {} s'.format(time_end - time_start))


if __name__ == '__main__':
    main()
