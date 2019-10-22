#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
ares_retrimp

Ares Retrieve-Import Tool with GUI
'''

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

import logging
logger = logging.getLogger()

import argparse
from ares.ares_retrieve.ares_retrieve import Retriever

VERSION = '0.0.2'

__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = VERSION
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""

# Default configuration
DefaultConfig = os.path.join(os.getenv('PYTHONPATH',
                                       '../../cfg').split(':'),
                             'retrieval_config.ini')

def configureLogs():
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
    for lname in os.environ['LOGGING_MODULES'].split(':'):
        lgr = logging.getLogger(lname)
        if not lgr.handlers: lgr.addHandler(c_handler)

def getArgs():
    '''
    Parse arguments from command line

    :return: args structure
    '''
    parser = argparse.ArgumentParser(description='ARES Data RetrieverTest script to retrieve data from ARES system',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config', dest='config_file', default=DefaultConfig,
                        help='Configuration file to use (default:{})'.format(DefaultConfig))
    parser.add_argument('-f', '--from_pid', dest='from_pid', type=int, default=1,
                        help='Initial parameter identifier')
    parser.add_argument('-t', '--to_pid', dest='to_pid', type=int, default=1000,
                        help='Final parameter identifier')
    parser.add_argument('-F', '--from_date', dest='from_date', type=int, nargs=5,
                        help='Initial date in the format Y DOY h m s')
    parser.add_argument('-T', '--to_date', dest='to_date', type=int, nargs=5,
                        help='Final date in the format Y DOY h m s')
    parser.add_argument('-n', '--num_pids_per_file', dest='num_pids_per_file', type=int,
                        default=100, help='Maximum number of PIDs per file')
    parser.add_argument('-e', '--sys_elem', dest='sys_elem', default='TM',
                        help='Set System Element (default:TM)')

    return parser.parse_args()

def greetings(output_dir, file_list):
    """
    Says hello
    """
    logger.info('='*60)
    logger.info('ares_retrimp - Retrieves a set of parameters from HMS data base into a FITS file')
    logger.info('='*60)

def main():
    """
    Main program
    """
    configureLogs()
    
    args = getArgs()
    
    # Set dates (add ms)
    fromDate = list(args.from_date) + [0]
    toDate = list(args.to_date) + [0]
    rqstm = 'pid'

    # File name template
    filename_tpl = 'ares_%F-%T_%f-%t_%YMD1T%hms1-%YMD2T%hms2'
    if rqstm == 'name':
        filename_tpl = 'ares_%F_%N_%YMD1T%hms1-%YMD2T%hms2'

    retriever = Retriever(cfg_file=args.config_file, rqst_mode='pid',
                          from_pid=args.from_pid, to_pid=args.to_pid,
                          pids_block=args.num_pids_per_file,
                          from_date=tuple(fromDate), to_date=tuple(toDate),
                          output_dir='./', file_tpl=filename_tpl,
                          sys_elem=args.sys_elem)
    retr_time_total, conv_time_total, full_time_total, param_names_invalid, gen_files = retriever.run()

    logger.info('Total retrieval time:  {:8d} s'.format(retr_time_total))
    logger.info('Total conversion time: {:8d} s'.format(conv_time_total))
    logger.info('Total processing time: {:8d} s'.format(full_time_total))
    logger.info('Invalid parameters: {}'.format(','.join(param_names_invalid)))
    logger.info('Generated files:')
    for file in gen_files:
        logger.info(' - {}'.format(file))


if __name__ == '__main__':
    main()
