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

from tkinter import *

PYTHON2 = False
PY_NAME = "python3"
STRING = str

#from appgui import App
from enum import Enum
from fnamespec.fnamespec.fnamespec import ProductMetadata
from datetime import datetime, timedelta
from utime.utime import datetime_to_ms, unix_ms_to_datestr
from shutil import copyfile
from astropy.table import Table
from astropy.io import fits

import ares.pyares as pa
import numpy as np

import argparse
import glob
import json
import time

import logging
logger = logging.getLogger()


VERSION = '0.0.2'

__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = VERSION
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""


# Correspondence ARES Types => FITS BinaryTable Types
Ares2FitsConversion = {
    '1':   'X',   # BIT
    '2':   'B',   # UTINYINT
    '3':   'B',   # STINYINT
    '4':   'I',   # USMALLINT
    '5':   'I',   # SSMALLINT
    '6':   'J',   # UMEDIUMINT
    '7':   'J',   # SMEDIUMINT
    '8':   'K',   # SINT
    '9':   'K',   # UINT
    '10':  'E',   # FLOAT
    '11':  'D',   # DOUBLE
    '12':  'A{}', # STRING
    '13':  '!',   # DATETIME
    '14':  '!',   # JOB
    '15':  '!'    # LOG
}
StringType = 12
DateTimeType = 13

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
    for lname in os.getenv('LOGGING_MODULES', '').split(':'):
        lgr = logging.getLogger(lname)
        if not lgr.handlers: lgr.addHandler(c_handler)

def get_args():
    '''
    Parse arguments from command line

    :return: args structure
    '''
    parser = argparse.ArgumentParser(description='Test script to enhance LE1 products',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config', dest='config_file',
                        help='Configuration file to use')
    parser.add_argument('-f', '--file', dest='input_file',
                        help='Input product')
    parser.add_argument('-d', '--dir', dest='input_dir',
                        help='Input files directory')
    parser.add_argument('-o', '--output', dest='output',
                        help='Output file name')
    parser.add_argument('-g', '--gui', dest='gui', default=False, action='store_true',
                        help='Output file name')
    return parser.parse_args()


#----------------------------------------------------------------------------
# Enum LE1ProductType: Internal format of file
#----------------------------------------------------------------------------
class LE1ProductType(Enum):
    UNKNOWN = ''
    VIS = 'VIS'
    NIR = 'NIR'
    SIR = 'SIR'

#----------------------------------------------------------------------------
# Enum TimeIntervalType: Type of time interval specification
#----------------------------------------------------------------------------
class TimeIntervalType(Enum):
    Undefined = ''
    Observation = 'observation'
    Modified = 'modified'
    UserDefined = 'user'

#----------------------------------------------------------------------------
# Enum DatasetAggregator: Operation to perform on dataset
#----------------------------------------------------------------------------
class Aggregator(Enum):
    Undefined  = ''
    # Single parameter metrics
    Count       = 'count'    # count how many values - default
    Sum         = 'sum'      # sum all the values
    Average     = 'avg'      # the average of the parameter over the time interval
    StDev       = 'stdev'    # the std.dev. of the parameter over the time interval
    Var         = 'var'      # the variance of the parameter over the time interval
    Min         = 'min'      # the minimum of the parameter over the time interval
    Max         = 'max'      # the maximum of the parameter over the time interval
    Median      = 'median'   # the median of the parameter over the time interval
    Summary     = 'summary'  # all the values above
    Table       = 'table'    # a new table is added with the data (def. for strings)
    Compressed  = 'compressed' # table, with only the points where the value changes
    Last        = 'last'     # last value in the interval
    First       = 'first'    # first value in the interval
    FirstLast   = 'first_last' # first and last values in the interval
    Linear      = 'linear'   # Coeficients of a linear fit in the form p = a x + b
    # 2-parameter metrics
    Corr        = 'corr'     # Correlation
    Distance    = 'dist'     # norm2 of the vector of differences
    AbsDistance = 'absdist'  # norm1 of the vector of differences
    SumProd     = 'sumprod'  # sum of the products

def splitFileName(file):
    fileinit, file_ext = os.path.splitext(file)
    file_path = os.path.dirname(fileinit)
    file_bname = os.path.basename(fileinit)
    return (file_path, file_bname + file_ext, file_bname, file_ext[1:])

#----------------------------------------------------------------------------
# Class LE1_FilesMetadataEnhancer
#----------------------------------------------------------------------------
class LE1_FilesMetadataEnhancer:
    '''
    Class to hold information and aggregation information for
    parmeters to be retrieved from HMS and stored as additional
    metadata into LE1 products.
    '''
    logger = logging.getLogger(__name__ + '.LE1_AdditionalParameter')
    if not logger.handlers: logger.addHandler(logging.NullHandler())

    def __init__(self, files, enhcfg):
        '''
        Initializer
        :param files: List of tuples with file names
        :param enhcfg: Configuration structure
        '''
        self.file_set = files
        self.convertCfgToParamRqsts(enhcfg)

    def convertCfgToParamRqsts(self, enhcfg):
        '''
        Function to convert config. to param. requests
        :param cfg: The parameters configuration
        :return: The parameters requests structure
        '''
        self.param_rqsts = {}
        for section in enhcfg['data'].keys():
            enhs = enhcfg['data'][section]
            p = {}
            for newpar, spec in enhs.items():
                # Get parameters to retrieve
                params = spec['parameter']

                # Get begin and end values ("user" not yet handled)
                delta = [0, 0]
                if TimeIntervalType(spec['timespan']['type']) == TimeIntervalType.Modified:
                    delta = [spec['timespan']['begin'],
                             spec['timespan']['end']]

                # Get aggregator
                aggr_name = Aggregator(spec['dataset']['mode'])
                aggr = self.getAggregator(aggr_name)

                p[newpar] = {'params': params, 'delta': delta,
                             'aggr_name': aggr_name, 'aggr': aggr}

            self.param_rqsts[section] = p

    def getAggregator(self, aggr=Aggregator.Sum):
        '''
        Aggregate one array of values into one or more output data values
        :param arr: Data values
        :param aggr: Aggregation method to use
        :return:
        '''
        # Single parameter metrics
        if   aggr == Aggregator.Count:
            return lambda a : max(a.shape)
        elif aggr == Aggregator.Sum:
            return lambda a : np.sum(a)
        elif aggr == Aggregator.Average:
            return lambda a: np.mean(a)
        elif aggr == Aggregator.StDev:
            return lambda a: np.std(a)
        elif aggr == Aggregator.Var:
            return lambda a: np.var(a)
        elif aggr == Aggregator.Min:
            return lambda a: np.min(a)
        elif aggr == Aggregator.Max:
            return lambda a: np.max(a)
        elif aggr == Aggregator.Median:
            return lambda a: np.median(a)
        elif aggr == Aggregator.Summary:
            return lambda a: {"count": max(a.shape),
                              "sum": np.sum(a),
                              "avg": np.mean(a),
                              "std": np.std(a),
                              "var": np.var(a),
                              "min": np.min(a),
                              "max": np.max(a),
                              "median": np.median(a)}
        elif aggr == Aggregator.Table:
            return None
        elif aggr == Aggregator.Compressed:
            return None
        elif aggr == Aggregator.Last:
            return lambda a: a[-1]
        elif aggr == Aggregator.First:
            return lambda a: a[0]
        elif aggr == Aggregator.FirstLast:
            return lambda a: [a[0], a[-1]]
        elif aggr == Aggregator.Linear:
            return lambda x, y: [np.linalg.lstsq(np.vstack([x, np.ones(len(x))]).T, y,
                                                 rcond=None)[0],
                                 np.corrcoef(x, y)[0, 1] ** 2]
        # 2-parameter metrics
        elif aggr == Aggregator.Corr:
            return lambda x, y: np.correlate(x, y)
        elif aggr == Aggregator.Distance:
            return lambda x, y: np.sqrt(np.sum(np.square(np.subtract(x, y))))
        elif aggr == Aggregator.AbsDistance:
            return lambda x, y: np.sum(np.fabs(np.subtract(x, y)))
        elif aggr == Aggregator.SumProd:
            return lambda x, y: np.sum(np.multiply(x, y))
        # Default - Count
        else:
            return lambda a : max(a.shape)

    def aggregate(self, dataset, aggr_name, aggr):
        '''
        Aggregate the dataset provided using the aggregator.
        For Single-parameter metrics, only the first parameter is used,
        For 2-parameter metrics, only the 2 first parameters are used.
        The rest of parameters, if any, are ignored (for the time being)
        :param dataset: The set of parameters (1 or 2)
        :param aggr: The aggregator to use
        :return:
        '''
        params = list(dataset.keys())

        if (aggr_name == Aggregator.Count or
            aggr_name == Aggregator.Sum or
            aggr_name == Aggregator.Average or
            aggr_name == Aggregator.StDev or
            aggr_name == Aggregator.Var or
            aggr_name == Aggregator.Min or
            aggr_name == Aggregator.Max or
            aggr_name == Aggregator.Median or
            aggr_name == Aggregator.Summary or
            aggr_name == Aggregator.Last or
            aggr_name == Aggregator.First or
            aggr_name == Aggregator.FirstLast):
            if len(params) < 1:
                logger.error("Cannot aggregate non-existing data")
                return None
            par = params[0]
            return aggr(dataset[par]['values']['data'])

        if (aggr_name == Aggregator.Corr or
            aggr_name == Aggregator.Distance or
            aggr_name == Aggregator.AbsDistance or
            aggr_name == Aggregator.SumProd):
            if len(params) < 2:
                logger.error("At least 2 parameters are needed for '{}' aggregator"
                             .format(aggr_name))
                return None
            par1 = params[0]
            par2 = params[1]
            return aggr(dataset[par1]['values']['data'],
                        dataset[par2]['values']['data'])

        if (aggr_name == Aggregator.Linear):
            if len(params) < 2:
                par = params[0]
                return aggr(dataset[par]['timestamp']['data'],
                            dataset[par]['values']['data'])
            else:
                par1 = params[0]
                par2 = params[1]
                return aggr(dataset[par1]['values']['data'],
                            dataset[par2]['values']['data'])

        return None

    def getTimeSpanFromFile(self, file):
        '''
        Get time range to use to retrieve parameter data
        :param file: Name of the input file
        :return: (t1, t2): Start and end time
        '''
        self.meta = self.prodMeta.parse(file)
        self.creator = self.meta['creator']
        datetime_start = 0
        datetime_end = 0
        if LE1ProductType(self.creator) == LE1ProductType.VIS:
            #datetime_str = self.meta['meta']['headers'][1]['DATE_OBS']
            datetime_str = '2018-07-17T00:00:00.000000'
            datetime_start = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
            #exptime_str = self.meta['meta']['headers'][1]['EXPTIME']
            exptime_str = '86400'
            datetime_end = datetime_start + timedelta(seconds=int(exptime_str))
        elif LE1ProductType(self.creator) == LE1ProductType.NIR:
            pass
        elif LE1ProductType(self.creator) == LE1ProductType.SIR:
            pass
        else:
            logger.error('Processing function "{}" not known.'.format(self.creator))
            return (None, None)

        return (datetime_start, datetime_end)

    def getParamData(self, params, starttime, endtime, syselem='TM'):
        '''
        Perform the retrieval of data for a given parameter and timespan
        '''
        var_name = ''
        var_type = ''

        starttime_ms = datetime_to_ms(starttime, 0)
        endtime_ms   = datetime_to_ms(endtime, 0)

        # Retrieve parameter samples as DataFrame
        logger.info('Retrieving data, param: {}.{}, time range: {} - {}'
                    .format(syselem, ','.join(params), starttime, endtime))
        syselems = [syselem] * len(params)
        samples = self.data_provider.get_parameter_sysel_data_objs(params, syselems,
                                                                   starttime_ms, endtime_ms)

        param_data = {}
        # Convert sample columns to binary tables
        i = 0
        for column in samples:

            pname = params[i]

            # Loop on samples to add values to the resulting vectors
            time_stamps = []
            values = []
            start = True

            for s in column:
                if start:
                    var_name = s.get_name()
                    var_type = s.get_type()
                    if var_name != pname:
                        logger.warning("ERROR: Param. name does not match with expectation!")
                    start = False

                time_stamps.append(s.get_time())

                value = s.get_value()
                if var_type == DateTimeType:
                    value = unix_ms_to_datestr(value)

                values.append(value)

                if var_type == DateTimeType:
                    var_type = StringType

            if start:
                logger.warning("ERROR: Could not retrieve data for parameter {}".format(pname))
                continue

            type_conv = Ares2FitsConversion[str(var_type)]
            if var_type == StringType:
                size_fld = len(max(values, key=len))
                type_conv = type_conv.format(size_fld if size_fld > 0 else 1)

            param_data[var_name] = {'timestamp': {'name': 'TIMESTAMP',
                                                  'data': np.array(time_stamps),
                                                  'format': 'K'},
                                    'values': {'name': var_name,
                                               'data': np.array(values),
                                               'format': type_conv}}
            i = i + 1

        return param_data

    def storeNewPar(self, hdr, newpar, meta, newparkwd):
        '''
        Add the name, values and comments for a new parameter in the FITS header
        :param hdr: The HD Unit in the FITS file
        :param newpar: New parameter name
        :param meta: New metadata information for the new param.
        :param newparkwd: New parameters keyword prefix
        :return:
        '''
        aggrdata = meta['aggr_data']
        aggrname = meta['aggr_name']
        if aggrdata:
            # Store new par name, with comment
            hdr[newparkwd] = (newpar, '{}({})'.format(aggrname, meta['params']))
            if aggrname == Aggregator.Summary:
                hdr[newparkwd + 'CNT'] = aggrdata['count']
                hdr[newparkwd + 'SUM'] = aggrdata['sum']
                hdr[newparkwd + 'AVG'] = aggrdata['avg']
                hdr[newparkwd + 'STD'] = aggrdata['std']
                hdr[newparkwd + 'VAR'] = aggrdata['var']
                hdr[newparkwd + 'MIN'] = aggrdata['min']
                hdr[newparkwd + 'MAX'] = aggrdata['max']
                hdr[newparkwd + 'MED'] = aggrdata['median']
            elif aggrname == Aggregator.Linear:
                hdr[newparkwd + '_M'] = (aggrdata[0][0], 'Slope of the linear model  y ~ m x + b')
                hdr[newparkwd + '_B'] = (aggrdata[0][1], 'Y-intercept of the linear model  y ~ m x + b')
                hdr[newparkwd + '_R2'] = (aggrdata[1], 'Correlation coefficient of the fit')
            else:
                hdr[newparkwd + 'VAL'] = aggrdata.item(0)
        elif aggrname == Aggregator.Table:
            pass
        elif aggrname == Aggregator.Compressed:
            pass
        else:
            logger.error('New metadata not found to store for "{}"'.format(newpar))

    def storeNewMetadata(self, file_tuple, new_meta):
        '''
        Store the new metadata in the output file.  If an "original" file
        name is provided, a copy of the initial file is saved with that name.
        :param file_tuple: File input/output/original names
        :param new_meta: New generated metadata
        :return:
        '''
        f_in, f_out, f_orig = file_tuple
        if f_orig:
            # Rename input file to original file name, and copy from that to output file
            os.rename(f_in, f_orig)
            copyfile(f_orig, f_out)
        else:
            # Just create a copy of the input as the output
            copyfile(f_in, f_out)

        with fits.open(f_out, mode='update') as hdul:
            i = 1
            for newpar, meta in new_meta.items():
                newparkwd = 'HMS{:02d}'.format(i)
                self.storeNewPar(hdul[0].header, newpar, meta, newparkwd)
                i = i + 1
            hdul.flush()

    def processFile(self, file_tuple):
        '''
        Process the entire set of files
        '''
        f_in, f_out, f_orig = file_tuple
        logger.info('Processing file {} . . .'.format(f_in))

        # Get initial time span for file
        time_start, time_end = self.getTimeSpanFromFile(file=f_in)
        if not time_start:
            logger.warning('Cannot process file "{}"'.format(f_in))
            return

        new_meta = {}

        # Loop over all new parameters defined for this type of products
        for newpar, rqst in self.param_rqsts[self.creator].items():
            # Build retrieval times
            t_start = time_start + timedelta(seconds=rqst['delta'][0])
            t_end   = time_end   + timedelta(seconds=rqst['delta'][1])

            # Build list of parameters to retrieve
            params = list(rqst['params'].split(','))

            # Retrieve data
            param_data = self.getParamData(params, t_start, t_end)

            # Aggregate data
            aggr_data = self.aggregate(param_data,
                                       rqst['aggr_name'],
                                       rqst['aggr'])

            new_meta[newpar] = {'data': param_data,
                                'params': rqst['params'],
                                'aggr_name': rqst['aggr_name'],
                                'aggr_data': aggr_data}

        # Finally, store new metadata information in output file
        self.storeNewMetadata(file_tuple, new_meta)
        logger.info('Ouptut written to {}'.format(f_out))

    def process(self):
        '''
        Process the entire set of files
        '''

        self.prodMeta = ProductMetadata()

        # Initalize the needed datasources.
        # Right now this is hardcoded into the initializer, so for config
        # you need to manage this yourself.
        self.data_provider = pa.init_param_sampleprovider()
        self.data_provider.set_system_element_as_any()

        for f_tuple in self.file_set:
            self.processFile(file_tuple=f_tuple)


def greetings(output_dir, file_list):
    '''
    Says hello
    '''
    logger.info('='*60)
    logger.info('le1_enchange - Add metadata to LE1 products from HMS parameters')
    logger.info('-'*60)
    logger.info('The output folder is: {}'.format(output_dir))
    logger.info('The following product enhancements will take place:')
    for f, fo, _ in file_list:
        logger.info('- {}'.format(f))
        logger.info('  => {}'.format(fo))
    logger.info('The original files will be renamed with an ".orig" suffix if needed')
    logger.info('-'*60)


def processArgs(args):
    '''
    Process arguments from command line
    :return: File list and configuration
    '''
    # Compose input files list
    input_files = []
    if args.input_file:
        input_files.append(os.path.realpath(args.input_file))
    if args.input_dir:
        [input_files.append(os.path.realpath(x))
                            for x in glob.glob(args.input_dir + '/*')]

    if not input_files:
        logger.critical('ERROR: No input files provided. Exiting.')
        sys.exit(1)

    # Check output file
    if not args.output:
        # Assume output dir is current dir
        output_dir = os.getcwd()
    else:
        output_dir = args.output
        if not os.path.isdir(output_dir):
            logger.critical('ERROR: Output directory {} does not exist. Exiting.'.format(output_dir))
            sys.exit(1)

    # Check config file
    if not args.config_file:
        logger.critical('ERROR: No configuration for product enhancement provided. Exiting.')
        sys.exit(1)

    # Build list of file names (input, output, and backup if needed)
    file_list = []
    for f in input_files:
        f_path, f_name, f_bname, f_ext = splitFileName(f)
        f_out = os.path.join(output_dir, f_name)
        f_orig = None
        if f == f_out:
            f_orig = os.path.join(output_dir, '{}.{}.{}'.format(f_bname, 'orig', 'ext'))
        file_list.append([f, f_out, f_orig])

    input_files.clear()

    # Read configuration
    enh_config = None
    with open(args.config_file, 'r') as cfgFp:
        enh_config = json.load(cfgFp)

    return file_list, output_dir, enh_config

def main():
    '''
    Main program
    '''
    configureLogs()

    args = get_args()

    if args.gui:
        #root = Tk()
        #app = App(parent=root)
        #root.mainloop()
        return

    file_list, output_dir, enh_config = processArgs(args)

    # Say hello, and list process parameters
    greetings(output_dir, file_list)

    # Create main object, and launch process
    le1enh = LE1_FilesMetadataEnhancer(file_list, enh_config)
    le1enh.process()

    # fn1 = le1enh.getAggregator(aggr=DatasetAggregator.Count)
    # fn2 = le1enh.getAggregator(aggr=DatasetAggregator.Summary)
    # fn3 = le1enh.getAggregator(aggr=DatasetAggregator.Distance)
    # fn4 = le1enh.getAggregator(aggr=DatasetAggregator.Linear)
    #
    # arr = np.array([1, 2, 4, 3, 5, 3, 6, 7, 7, 8, 9])
    # arr2 = np.array([1.4, 2.2, 4.7, 3.7, 5.5, 3.1, 6.2, 7.3, 7.6, 8.3, 9.8])
    # print(arr)
    # print(fn1(arr))
    # print(fn2(arr))
    # print(fn3(arr, arr2))
    # print(fn4(arr, arr2))


if __name__ == '__main__':
    main()
