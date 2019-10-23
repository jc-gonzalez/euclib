#!/usr/bin/python
# -*- coding: utf-8 -*-
'''test3-jc.py.py

Test script to retrieve data from ARES system

Usage: test3-jc.py [-h] [-c CONFIG_FILE] [-f FROM_PID] [-t TO_PID]
                   [-F FROM_PID FROM_PID FROM_PID FROM_PID FROM_PID]
                   [-T TO_PID TO_PID TO_PID TO_PID TO_PID]

PyArEx package test script

optional arguments:
  -h, --help                               Show this help  message and exit
  -c CONFIG_FILE, --config CONFIG_FILE     Configuration file to use
                                           (default:pyarex.ini)
  -f FROM_PID, --from_pid FROM_PID         Initial parameter identifier
  -t TO_PID, --to_pid TO_PID               Final parameter identifier
  -F Y DOY h m s, --from_date Y DOY h m s  Initial date in the format Y DOY h m s
  -T Y DOY h m s, --to_date Y DOY h m s    Final date in the format Y DOY h m s
  -e SYS_ELEM                              Define system element (default:TM)

Usage example:

  $ python test3-jc.py -c ./cfg.ini -f 1 -t 2 -F 2013 354 0 0 0 -T 2013 354 1 0 0
'''

from astropy.table import Table
from astropy.io import fits

from utime.utime import *

import ares.pyares as pa
#import pandas as pd
import numpy as np
#import fitsio
#import matplotlib.pyplot as plt

import os, sys, errno
import argparse
import time
import gzip

import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype"  # Prototype | Development | Production


# Default configuration
DefaultConfig = 'pyarex.ini'

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

XMLTemplates = {
    'XML': """
<dpd-le1-hktm:HKTMProduct
    xmlns:pro-le1-vis="http://euclid.esa.org/schema/pro/le1/vis"
    xmlns:bas-imp-stc="http://euclid.esa.org/schema/bas/imp/stc"
    xmlns:sys="http://euclid.esa.org/schema/sys"
    xmlns:bas-utd="http://euclid.esa.org/schema/bas/utd"
    xmlns:bas-imp="http://euclid.esa.org/schema/bas/imp"
    xmlns:pro-le1="http://euclid.esa.org/schema/pro/le1"
    xmlns:bas-imp-fits="http://euclid.esa.org/schema/bas/imp/fits"
    xmlns:dpd-le1-visrawframe="http://euclid.esa.org/schema/dpd/le1/visrawframe"
    xmlns:ins="http://euclid.esa.org/schema/ins"
    xmlns:bas-imp-eso="http://euclid.esa.org/schema/bas/imp/eso"
    xmlns:bas-img="http://euclid.esa.org/schema/bas/img"
    xmlns:bas-ppr="http://euclid.esa.org/schema/bas/ppr"
    xmlns:bas-dtd="http://euclid.esa.org/schema/bas/dtd"
    xmlns:bas-cot="http://euclid.esa.org/schema/bas/cot"
    xmlns:sys-dss="http://euclid.esa.org/schema/sys/dss"
    xmlns:bas-dqc="http://euclid.esa.org/schema/bas/dqc"
    xmlns:bas-fit="http://euclid.esa.org/schema/bas/fit"
    xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <Header>
    <ProductId>{}</ProductId>
    <ProductType>HKTM</ProductType>
    <SoftwareName>HKTMProductGenerator</SoftwareName>
    <SoftwareRelease>2.2</SoftwareRelease>
    <ManualValidationStatus>UNKNOWN</ManualValidationStatus>
    <PipelineRun></PipelineRun>
    <ExitStatusCode>0</ExitStatusCode>
    <DataModelVersion>N</DataModelVersion>
    <MinDataModelVersion>M</MinDataModelVersion>
    <ScientificCustodian>SOC</ScientificCustodian>
    <AccessRights>
      <EuclidConsortiumRead>True</EuclidConsortiumRead>
      <EuclidConsortiumWrite>False</EuclidConsortiumWrite>
      <ScientificGroupRead>False</ScientificGroupRead>
      <ScientificGroupWrite>False</ScientificGroupWrite>
    </AccessRights>
    <Curator>
      <Name>J.C.Gonzalez</Name>
      <Email>JCGonzalez@sciops.esa.int</Email>
    </Curator>
    <Creator>SOC</Creator>
    <CreationDate>{}</CreationDate>
  </Header>
  <Data>
    <DateTimeRange>
{}
    </DateTimeRange>
    <ParameterRange>
{}
    </ParameterRange>
    <ParameterList>
{}
    </ParameterList>
    <ProductList>
{}
    </ProductList>
  </Data>
</dpd-le1-hktm:HKTMProduct>
""",
    'DateTimeRange': '      <FromYDoY>{:04d}.{:03d} {:02d}:{:02d}:{:06.3f}Z</FromYDoY>\n' +
                     '      <ToYDoY>{:04d}.{:03d} {:02d}:{:02d}:{:06.3f}Z</ToYDoY>',
    'PIDRange': '      <FromPID>{}</FromPID>\n      <ToPID>{}</ToPID>',
    'Param': '      <Parameter pid="{}" name="{}" type="{}" prodIndex="{}" hduIndex="{}"/>',
    'Prod': '      <Product index="{}" baseName="{}" fromPID="{}" toPID="{}">\n{}\n      </Product>',
    'HDU': '        <HDU index="{}" pid="{}" paramName="{}" type="{}"/>'
}

def silent_remove(filename):
    '''
    Silently remove file if it does exist
    '''
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred


def gzip_file(src_path, dst_path):
    '''
    Gzip file to file.gz

    :param src_path: Existing file
    :param dst_path: Compressed file
    '''
    with open(src_path, 'rb') as src, gzip.open(dst_path, 'wb') as dst:
        for chunk in iter(lambda: src.read(10240), b""):
            dst.write(chunk)

    os.remove(src_path)


#----------------------------------------------------------------------------
# Class: Retriever
#----------------------------------------------------------------------------
class Retriever(object):
    '''
    Simple class to perform an actual data retrieval from the ARES cluster,
    with the help of the PyArEx package.
    '''

    # Framework environment related variables
    Home = os.environ['HOME']
    AresRuntimeDir = ''

    if os.path.isdir(Home + '/ARES_RUNTIME'):
        AresRuntimeDir = Home + '/ARES_RUNTIME'

    if "ARES_RUNTIME" in os.environ:
        # Nominally, the QPFWA env. variable should point to the QPF Working Area
        # main directory (usually /home/eucops/qpf)
        AresRuntimeDir = os.environ["ARES_RUNTIME"]

    # The following hash table shows a series of regular expresions that can be used
    # to deduce the imported data file type
    AresFileTypes = {}
    AresFileTypesCfgFile = "import_file_types.json"

    def __init__(self, cfg_file=None, rqst_mode='pid',
                 from_pid=None, to_pid=None, pids_block=None, names=None,
                 from_date=None, to_date=None, sys_elem='TM',
                 output_dir='./',
                 file_tpl='ares_%F-%T_%f-%t_%YMD1T%hms1-%YMD2T%hms2',
                 file_type='fits'):
        '''
        Instance initialization method
        '''
        # Define config. file if not set in the local environment
        if cfg_file == None:
            if not 'PYAREX_INI_FILE' in os.environ:
                os.environ['PYAREX_INI_FILE'] = cfg_file
        else:
            os.environ['PYAREX_INI_FILE'] = cfg_file

        logger.info('Reading retrieval script config. file {0}'.format(cfg_file))

        self.rqst_mode = rqst_mode

        self.param_names = names

        if self.rqst_mode == 'pid':
            self.from_pid = from_pid
            self.to_pid = to_pid
            self.pid_blk = pids_block
            self.from_pid_blk = self.from_pid
            self.to_pid_blk = self.from_pid_blk + self.pid_blk - 1
            self.name = ''
        else:
            self.from_pid, self.to_pid = (1, 1)
            self.from_pid_blk, self.to_pid_blk, self.pid_blk = (1, 1, 1)
            self.name = 'PARAM'

        logger.info(f'From date {from_date} to date {to_date}')
        if len(from_date) == 6:
            self.year1, self.doy1, self.hour1, self.min1, self.sec1, msec = from_date
        else:
            self.year1, mnth, mday, self.hour1, self.min1, self.sec1, msec = from_date
            self.year1, self.doy1 = ymd_to_ydoy(self.year1, mnth, mday)
        self.timestamp_start = unix_ydoy_to_ms(self.year1, self.doy1, self.hour1, self.min1, self.sec1, msec)
        self.sec1 = self.sec1 + msec * 0.001
        year, self.month1, self.day1 = ydoy_to_ymd(self.year1, self.doy1)

        if len(to_date) == 6:
            self.year2, self.doy2, self.hour2, self.min2, self.sec2, msec = to_date
        else:
            self.year2, mnth, mday, self.hour2, self.min2, self.sec2, msec = to_date
            self.year2, self.doy2 = ymd_to_ydoy(self.year2, mnth, mday)
        self.timestamp_end = unix_ydoy_to_ms(self.year2, self.doy2, self.hour2, self.min2, self.sec2, msec)
        self.sec2 = self.sec2 + msec * 0.001
        year, self.month2, self.day2 = ydoy_to_ymd(self.year2, self.doy2)

        self.outdir = output_dir
        self.file_tpl = self.create_actual_file_tpl(file_tpl)
        #print(self.generate_filename(self.file_tpl))
        self.file_type = file_type

        self.xmlDateTimeRange = XMLTemplates['DateTimeRange'].format(self.year1, self.doy1,
                                                                     self.hour1, self.min1, self.sec1,
                                                                     self.year2, self.doy2,
                                                                     self.hour2, self.min2, self.sec2)
        self.xmlPIDRange = XMLTemplates['PIDRange'].format(self.from_pid, self.to_pid)

        self.xmlHDUs = []
        self.xmlParams = []
        self.xmlProds = []

        logger.info('-'*60)
        logger.info("Retrieving samples for parameters with parameter ids in the range {0}:{1}"
                     .format(from_pid, to_pid))
        logger.info("from the date {0}.{1}.{2:02d}:{3:02d}:{4:06.3f}"
                     .format(self.year1, self.doy1, self.hour1, self.min1, self.sec1))
        logger.info("to the date {0}.{1}.{2:02d}:{3:02d}:{4:06.3f}"
                     .format(self.year2, self.doy2, self.hour2, self.min2, self.sec2))
        logger.info("and storing the data in FITS files, in blocks of {0} param.ids"
                     .format(self.pid_blk))
        logger.info('-'*60)

    def run(self):
        '''
        Execute the retrieval
        '''
        if self.rqst_mode == 'pid':
            results = self.run_retrieval_pids()
        else:
            results = self.run_retrieval_names()

        return results

    def run_retrieval_pids(self):
        '''
        Perform the retrieval of a range of PIDs
        '''

        # Get start time
        start_time = time.time()
        end_time = start_time

        # Initalize the needed datasources.
        # Right now this is hardcoded into the initializer, so for config
        # you need to manage this yourself.
        data_provider = pa.init_param_sampleprovider()
        data_provider.set_system_element_as_any()

        retr_time_total, conv_time_total = (0, 0)

        keep_retrieving = True
        i_pid = self.from_pid
        j_pid = i_pid + self.pid_blk - 1
        param_names_invalid = {}
        gen_files = []
        var_name = ''
        var_type = ''

        nfile = 1

        while keep_retrieving:

            # Set preparation time stamp
            prep_time = time.time()

            # Get parameter names for the range of parameter ids, and retrieve samples as DataFrame
            (param_names, param_syselem) = data_provider.get_parameter_names_from_pids(i_pid, j_pid)
            samples = data_provider.get_parameter_sysel_data_objs(param_names,
                                                                  param_syselem,
                                                                  self.timestamp_start,
                                                                  self.timestamp_end)

            # Set retrieval time stamp
            retr_time = time.time()

            # Currently only FITS files are generated

            # Build initial primary HDU for FITS file
            hdul = self.fits_build_hdr(i_pid, j_pid)

            # Convert sample columns to binary tables
            i = 0
            pid = i_pid

            for column in samples:

                # Loop on samples to add values to the resulting vectors
                time_stamps = []
                values = []
                start = True

                for s in column:
                    if start:
                        var_name = s.get_name()
                        var_type = s.get_type()
                        if var_name != param_names[i]:
                            logger.warning("ERROR: Param. name does not match with expectation!")
                        logger.info('Generating table {} of {} for PID {} - {} (type={})'
                                     .format(i + 1, self.pid_blk, pid, var_name, var_type))
                        start = False

                    time_stamps.append(s.get_time())

                    value = s.get_value()
                    if var_type == DateTimeType:
                        value = unix_ms_to_datestr(value)

                    values.append(value)

                    if var_type == DateTimeType:
                        var_type = StringType

                i = i + 1
                pid = pid + 1

                if start:
                    param_names_invalid[str(pid - 1)] = param_names[i - 1]
                    continue

                type_conv = Ares2FitsConversion[str(var_type)]
                if var_type == StringType:
                    size_fld = len(max(values, key=len))
                    type_conv = type_conv.format(size_fld if size_fld > 0 else 1)

                t = fits.BinTableHDU.from_columns([fits.Column(name='TIMESTAMP',
                                                               array=np.array(time_stamps),
                                                               format='K'),
                                                   fits.Column(name=var_name,
                                                               array=np.array(values),
                                                               format=type_conv)])
                hdul.append(t)

                # Generate XML index section
                self.xmlHDUs.append(XMLTemplates['HDU'].format(i, pid-1, var_name, type_conv))
                self.xmlParams.append(XMLTemplates['Param'].format(pid-1, var_name, type_conv,
                                                                   nfile, i))

            # Remove FITS file if exists, and (re)create it
            self.from_pid_blk, self.to_pid_blk = (i_pid, j_pid)
            base_name = self.generate_filename(self.file_tpl)
            file_name = os.path.join(self.outdir, base_name) + '.fits'
            self.save_to_fits(hdul, file_name)
            gen_files.append(file_name)
            logger.info('Saved file {}'.format(file_name))

            self.xmlProds.append(XMLTemplates['Prod'].format(nfile, base_name,
                                                             self.from_pid_blk, self.to_pid_blk,
                                                             '\n'.join(self.xmlHDUs)))
            self.xmlHDUs = []

            nfile = nfile + 1
            end_time = time.time()

            retr_time_total = retr_time_total + (retr_time - start_time)
            conv_time_total = conv_time_total + (end_time - retr_time)

            i_pid = j_pid + 1
            j_pid = i_pid + self.pid_blk - 1
            if j_pid > self.to_pid:
                j_pid = self.to_pid

            keep_retrieving = (i_pid < self.to_pid)

        full_time_total = end_time - start_time

        logger.info("Data retrieval:   {:10.3f} s".format(retr_time_total))
        logger.info("Data conversion:  {:10.3f} s".format(conv_time_total))
        logger.info("Total exec. time: {:10.3f} s".format(full_time_total))
        if len(param_names_invalid) > 0:
            logger.info("The following parameters could not be converted:")
            for p in param_names_invalid.keys():
                logger.info('{}: "{}"'.format(p, param_names_invalid[p]))

        # Generate complete XML index file
        xml_file_tpl = self.create_actual_file_tpl('EUC_SOC_HKTM_%YMD1T%hms1-%YMD2T%hms2')
        base_name = self.generate_filename(xml_file_tpl)
        xml = XMLTemplates['XML'].format(base_name, now_utc_iso(),
                                         self.xmlDateTimeRange, self.xmlPIDRange,
                                         '\n'.join(self.xmlParams),
                                         '\n'.join(self.xmlProds))
        xml_file = os.path.join(self.outdir, base_name) + '.xml'
        with open(xml_file, "w") as fxml:
            fxml.write(xml)

        return (retr_time_total, conv_time_total, full_time_total, param_names_invalid, gen_files)

    def run_retrieval_names(self):
        '''
        Perform the retrieval of a range of PIDs
        '''

        # Get start time
        start_time = time.time()
        end_time = start_time

        # Initalize the needed datasources.
        # Right now this is hardcoded into the initializer, so for config
        # you need to manage this yourself.
        data_provider = pa.init_param_sampleprovider()
        data_provider.set_system_element_as_any()

        retr_time_total, conv_time_total = (0, 0)

        param_names_invalid = {}
        gen_files = []
        var_name = ''
        var_type = ''

        # Set preparation time stamp
        prep_time = time.time()

        # Get parameter names for the range of parameter ids, and retrieve samples as DataFrame
        (param_pids, param_syselem) = data_provider.get_parameter_pid_sysel_from_names(self.param_names)
        samples = data_provider.get_parameter_sysel_data_objs(self.param_names,
                                                              param_syselem,
                                                              self.timestamp_start,
                                                              self.timestamp_end)

        # Set retrieval time stamp
        retr_time = time.time()

        # Convert sample columns to binary tables
        i = 0
        for column in samples:

            pname = self.param_names[i]
            pid = param_pids[i]

            # Currently only FITS files are generated

            # Build initial primary HDU for FITS file
            hdul = self.fits_build_hdr(pid, pid)

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
                    logger.info('Generating table for PID {} - {} (type={})'
                                 .format(pid, var_name, var_type))
                    start = False

                time_stamps.append(s.get_time())

                value = s.get_value()
                if var_type == DateTimeType:
                    value = unix_ms_to_datestr(value)

                values.append(value)

                if var_type == DateTimeType:
                    var_type = StringType

            if start:
                param_names_invalid[str(pid - 1)] = pname
                continue

            type_conv = Ares2FitsConversion[str(var_type)]
            if var_type == StringType:
                size_fld = len(max(values, key=len))
                type_conv = type_conv.format(size_fld if size_fld > 0 else 1)

            t = fits.BinTableHDU.from_columns([fits.Column(name='TIMESTAMP',
                                                           array=np.array(time_stamps),
                                                           format='K'),
                                               fits.Column(name=var_name,
                                                           array=np.array(values),
                                                           format=type_conv)])
            hdul.append(t)

            # Remove FITS file if exists, and (re)create it
            self.from_pid, self.to_pid = (pid, pid)
            self.from_pid_blk, self.to_pid_blk = (pid, pid)
            self.name = pname
            base_name = self.generate_filename(self.file_tpl)
            file_name = os.path.join(self.outdir, base_name) + '.fits'
            self.save_to_fits(hdul, file_name)
            gen_files.append(file_name)
            logger.info('Saved file {}'.format(file_name))

            # Generate XML index section
            self.xmlParams.append(XMLTemplates['Param'].format(pid, var_name, type_conv, i + 1, i + 1))
            self.xmlHDUs.append(XMLTemplates['HDU'].format(i + 1, pid, var_name, type_conv))
            self.xmlProds.append(XMLTemplates['Prod'].format(i + 1, base_name,
                                                             self.from_pid_blk, self.to_pid_blk,
                                                             '\n'.join(self.xmlHDUs)))
            self.xmlHDUs = []

            # Go on
            i = i + 1

            end_time = time.time()

            retr_time_total = retr_time_total + (retr_time - start_time)
            conv_time_total = conv_time_total + (end_time - retr_time)

        full_time_total = end_time - start_time

        logger.info("Data retrieval:   {:10.3f} s".format(retr_time_total))
        logger.info("Data conversion:  {:10.3f} s".format(conv_time_total))
        logger.info("Total exec. time: {:10.3f} s".format(full_time_total))
        if len(param_names_invalid) > 0:
            logger.info("The following parameters could not be converted:")
            for p in param_names_invalid.keys():
                logger.info('{}: "{}"'.format(p, param_names_invalid[p]))

        # Generate complete XML index file
        xml_file_tpl = self.create_actual_file_tpl('EUC_SOC_HKTM_%YMD1T%hms1-%YMD2T%hms2')
        base_name = self.generate_filename(xml_file_tpl)
        xml = XMLTemplates['XML'].format(base_name, 'NOW',
                                         self.xmlDateTimeRange, self.xmlPIDRange,
                                         '\n'.join(self.xmlParams),
                                         '\n'.join(self.xmlProds))
        xml_file = os.path.join(self.outdir, base_name) + '.xml'
        with open(xml_file, "w") as fxml:
            fxml.write(xml)

        return (retr_time_total, conv_time_total, full_time_total, param_names_invalid, gen_files)

    def create_actual_file_tpl(self, tpl):
        '''
        The filename template uses the following placeholders:
        - %F : Starting pid of the retrieval
        - %f : Starting pid of the file
        - %t : End pid of the file
        - %T : End pid of the retrieval
        - %b : Block size
        - %Y1 : Starting year
        - %D1 : Starting day of year
        - %M1 : Starting month
        - %d1 : Starting day
        - %h1 : Starting hour
        - %m1 : Starting minute
        - %s1 : Starting second
        - %Y2 : End year
        - %D2 : End day of year
        - %M2 : End month
        - %d2 : End day
        - %h2 : End hour
        - %m2 : End minute
        - %s2 : End second
        - %YMD1 : Starting date in YYYYMMDD format
        - %YDoY1 : Starting date in YYYYDoY format
        - %YMD2 : End date in YYYYMMDD format
        - %YDoY2 : End date in YYYYDoY format
        - %hms1 : Start time in HHMMSS format
        - %hms2 : End time in HHMMSS format
        This method transforms a template with these placeholders in a template that
        can be used with str.format()
        '''
        template_placeholders = {
                                 '%F': '{from_pid}',     # Starting pid of the retrieval
                                 '%f': '{from_pid_blk}', # Starting pid of the file
                                 '%t': '{to_pid_blk}',   # End pid of the file
                                 '%T': '{to_pid}',       # End pid of the retrieval
                                 '%b': '{pid_blk}',      # Block size
                                 '%N': '{name}',         # Param. name
                                 '%Y1': '{year1:04d}',   # Starting year
                                 '%D1': '{doy1:02d}',    # Starting day of year
                                 '%M1': '{month1:02d}',  # Starting month
                                 '%d1': '{day1:02d}',    # Starting day
                                 '%h1': '{hour1:02d}',   # Starting hour
                                 '%m1': '{min1:02d}',    # Starting minute
                                 '%s1': '{sec1:02d}',    # Starting second
                                 '%Y2': '{year2:04d}',   # End year
                                 '%D2': '{doy2:02d}',    # End day of year
                                 '%M2': '{month2:02d}',  # End month
                                 '%d2': '{day2:02d}',    # End day
                                 '%h2': '{hour2:02d}',   # End hour
                                 '%m2': '{min2:02d}',    # End minute
                                 '%s2': '{sec2:02d}',    # End second
                                 '%YMD1': '{year1:04d}{month1:02d}{day1:02d}', # Starting date in YYYYMMDD format
                                 '%YDoY1': '{year1:04d}{doy1:02d}', # Starting date in YYYYDoY format
                                 '%YMD2': '{year2:04d}{month2:02d}{day2:02d}', # End date in YYYYMMDD format
                                 '%YDoY2': '{year2:04d}{doy2:02d}', # End date in YYYYDoY format
                                 '%hms1': '{hour1:02d}{min1:02d}{sec1:02d}', # Start time in HHMMSS format
                                 '%hms2': '{hour2:02d}{min2:02d}{sec2:02d}' # End time in HHMMSS format
                                 }

        for ph, named in template_placeholders.items():
            tpl = tpl.replace(ph, named)

        return tpl

    def generate_filename(self, tpl):
        return tpl.format(from_pid=self.from_pid, from_pid_blk=self.from_pid_blk,
                          to_pid_blk=self.to_pid_blk, to_pid=self.to_pid,
                          pid_blk=self.pid_blk,
                          name=self.name,
                          year1=self.year1, doy1=self.doy1,
                          month1=self.month1, day1=self.day1,
                          hour1=self.hour1, min1=self.min1, sec1=int(self.sec1),
                          year2=self.year2, doy2=self.doy2,
                          month2=self.month2, day2=self.day2,
                          hour2=self.hour2, min2=self.min2, sec2=int(self.sec2))

    def fits_build_hdr(self, i, j):
        '''
        Build FITS header for resulting file
        '''
        # Build initial primary HDU for FITS file
        hdr = fits.Header()
        hdr['OBSERVER'] = 'Euclid Operator'
        hdr['COMMENT'] = 'Multitable FITS file, with data retrieved fro ARES system'
        hdr['COMMENT'] = 'File contains data for PIDs in range {}:{}'.format(i, j)
        primary_hdu = fits.PrimaryHDU(header=hdr)
        return fits.HDUList([primary_hdu]) # HDU List with only primary_hdu

    def save_to_fits(self, hdu_list, file_name):
        '''
        Save HDU List to FITS file
        '''
        silent_remove(file_name)
        hdu_list.writeto(file_name)

def main():
    pass

if __name__ == '__main__':
    main()
