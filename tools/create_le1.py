#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create-le1.py

Dummy LE1 processor for LE1 creation
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

import time
import argparse

from datetime import datetime

#import json

import logging
FORMAT = '%(asctime)s %(levelname).1s %(name)s %(module)s:%(lineno)d %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
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

def getArgs():
    """
    Parse arguments from command line

    :return: args structure
    """
    parser = argparse.ArgumentParser(description='Dummy LE1 Processor',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_file', dest='input_file',
                        help='Input file name (without path)')
    parser.add_argument('-o', '--output_dir', dest='output_dir',
                        help='Output target directory')
    parser.add_argument('-w', '--work_dir', dest='work_dir',
                        help='Working directory')
    return parser.parse_args()

def greetings():
    """
    Show log header
    :return: -
    """
    logger.info("==============================================================================")
    logger.info("create-le1 - Dummy LE1 processor for LE1 creation")
    logger.info("{}".format(__copyright__))
    logger.info("Last update {}".format(__date__))
    logger.info("Created by {} - {}".format(__author__, __email__))
    logger.info("==============================================================================")

def log(f, msg):
    f.write('{} I {}\n'.format(datetime.now().isoformat(), msg))

def replaceMultiple(mainString, toBeReplaces, newString):
    for elem in toBeReplaces:
        if elem in mainString:
            mainString = mainString.replace(elem, newString)
    return mainString

def normalize(file):
    return replaceMultiple(file, ['.', ' ', '-', '_'], '')

def main():
    """
    Main processor program
    """

    # Parse command line arguments
    args = getArgs()

    # Start message
    greetings()

    # Start time
    logger.info('Start!')
    time_start = time.time()

    # Create LE1 product and low
    output_file = 'EUC_LE1_VIS-12345-1-W-{}_{}.0Z.fits'.format(normalize(args.input_file),
                                                               datetime.now().strftime("%Y%m%dT%H%M%S"))
    file_out = os.path.join(args.output_dir, output_file)
    file_out_temp = file_out + '.part'
    file_log = os.path.join(args.output_dir, output_file.replace('.fits', '.log'))

    logger.info('Input file: {}'.format(args.input_file))
    logger.info('Output product: {}'.format(output_file))
    logger.info('Starting process . . .')

    with open(file_log, 'w') as flog:
        log(flog, 'Start.')
        log(flog, 'Creating product . . .')
        log(flog, 'Processing {}'.format('args.input_file'))
        with open(file_out_temp, 'w') as fout:
            fout.write('This is the LE1 product just created')
        log(flog, 'Done.')

    os.rename(file_out_temp, file_out)

    logger.info('LE1 product {} created . . .'.format(file_out))

    # End time, closing
    time_end = time.time()
    logger.info('Done.')
    logger.info('Ellapsed time: {} s'.format(time_end - time_start))


if __name__ == '__main__':
    main()
