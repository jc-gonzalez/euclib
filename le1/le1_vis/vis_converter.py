#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
le1_vis.py

Module with the LE1 VIS Data structures
"""
#----------------------------------------------------------------------

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

# System
import os
import sys
import logging
import argparse

from pprint import pprint

from le1_vis import InputType, OutputType, \
    InputTypeStrChoices, OutputTypeStrChoices
from raw2vis import RAW_to_VIS_Processor

#----------------------------------------------------------------------

PKG_FILEDIR = os.path.dirname(__file__)
PKG_APPSDIR, _ = os.path.split(PKG_FILEDIR)
PKG_BASEDIR, _ = os.path.split(PKG_APPSDIR)
sys.path.insert(0, os.path.abspath(os.path.join(PKG_FILEDIR, PKG_BASEDIR,
                                                PKG_APPSDIR)))

PYTHON2 = False
PY_NAME = "python3"
STRING = str

logger = logging.getLogger()

#----------------------------------------------------------------------

VERSION = '0.0.1'

__author__ = "J C Gonzalez"
__version__ = VERSION
__license__ = "LGPL 3.0"
__status__ = "Development"
__copyright__ = "Copyright (C) 2015-2019 by Euclid SOC Team @ ESAC / ESA"
__email__ = "jcgonzalez@sciops.esa.int"
__date__ = "June 2019"
__maintainer__ = "J C Gonzalez"
#__url__ = ""

#----------------------------------------------------------------------

def configure_logs():
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
    for lname in os.getenv('LOGGING_MODULES', '').split(':'):
        lgr = logging.getLogger(lname)
        if not lgr.handlers: lgr.addHandler(c_handler)

def get_args():
    """
    Parse arguments from command line

    :return: args structure
    """
    parser = argparse.ArgumentParser(description='Test script to enhance LE1 products',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--from', dest='itype',
                        choices=InputTypeStrChoices, default='raw',
                        help='String specifying the initial file format')
    parser.add_argument('-t', '--to', dest='otype',
                        choices=OutputTypeStrChoices, default='le1',
                        help='String specifying the final file format')
    parser.add_argument('-i', '--input_file', dest='input_file',
                        help='Input file name')
    parser.add_argument('-o', '--output_dir', dest='output_dir',
                        help='Output file directory', default='.')
    return parser.parse_args()

def greetings():
    """
    Says hello
    """
    logger.info('='*60)
    logger.info('vis_converter - Convert RAW to VIS, or adapts LE1 to another baseline')
    logger.info('-'*60)

def parse_args():
    """
    Configure the parameters for the RAW => LE1 processing
    :return: The complete argparse structure
    """
    args = get_args()

    args.input_type = InputType.inputType(args.itype)
    if args.input_type == InputType.UNKNOWN:
        logger.fatal(f'Non-supported input file type "{args.itype}"')

    args.output_type = OutputType.outputType(args.otype)
    if args.output_type == InputType.UNKNOWN:
        logger.fatal(f'Non-supported output file type "{args.itype}"')

    if args.input_type == InputType.LE1:
        logger.fatal('Adaptation of an input LE1 is not yet supported')

    return args


def main():
    """
    Main program
    """
    configure_logs()

    args = parse_args()

    # Say hello, and list process parameters
    greetings()

    # Create main object, and launch process
    converter = RAW_to_VIS_Processor(args)
    converter.run()


if __name__ == '__main__':
    main()
