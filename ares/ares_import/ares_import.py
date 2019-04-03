#!/usr/bin/python
# -*- coding: utf-8 -*-
'''ares_importer

Package to help to the data files import process'''

from shutil import copy
from pprint import pprint

import os, sys
import logging
import re
import time
import glob
import json

VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


# Change INFO for DEBUG to get debug messages
log_level = logging.DEBUG

# Set up logging information
format_string = '%(asctime)s %(levelname).1s %(message)s'
logging.basicConfig(level=log_level, format=format_string, stream=sys.stderr)


#----------------------------------------------------------------------------
# Class: Importer
#----------------------------------------------------------------------------
class Importer(object):
    '''
    Processor is the base class for all the processors to be executed from
    the Euclid QLA Processing Framework, independent if they are run inside or
    outside Docker containers.
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

    def __init__(self, data_dir=None, input_file=None, desc_file=None,
                 ares_runtime=None, import_dir=None, data_type=None,
                 batch_mode=False, cfg_file=None):
        '''
        Instance initialization method
        '''

        # Get arguments, and incorporate to object
        self.data_dir = data_dir
        self.ares_runtime = Importer.AresRuntimeDir
        self.data_type = data_type
        self.desc_file = desc_file
        self.input_file = input_file

        self.batch_mode = batch_mode

        self.num_of_files = 1
        self.num_of_imported_files = 0
        self.num_of_failed_files = 0
        self.ares_data_types = {}
        self.hasCompiledPatterns = False

        if not cfg_file:
            this_script_dir = os.path.dirname(os.path.realpath(__file__))
            cfg_file = this_script_dir + '/../' + Importer.AresFileTypesCfgFile
        
        logging.info('Reading import script config. file {0}'.format(cfg_file))
        try:
            with open(cfg_file) as fcfg:
                try:
                    self.ares_data_types = json.load(fcfg)
                    self.compile_patterns()
                    self.hasCompiledPatterns = True
                except:
                    self.error_msg('Problem while reading config. file {0}'
                              .format(cfg_file))
        except:
            self.error_msg('Import script config. file not found in {0}'
                      .format(cfg_file))

        logging.info('-'*60)

        if ares_runtime:
            self.ares_runtime = ares_runtime

        if not os.path.isdir(self.ares_runtime):
            self.error_msg('ARES system runtime folder {0} does not exist'
                      .format(self.ares_runtime))

        logging.info('ARES system runtime folder is {0}'.format(self.ares_runtime))
        self.ares_import = self.ares_runtime + '/import'
        logging.info('ARES import folder is {0}'.format(self.ares_import))

        self.admin_server_log = self.ares_runtime + '/AdminServer/AdminServer.log'
        logging.info('Monitoring ARES Server log file {0}'.format(self.admin_server_log))

        # Evaluate input data files
        if data_dir:
            if not os.path.isdir(self.data_dir):
                self.error_msg('Specified input data folder {0} does not exist'
                          .format(self.data_dir))

            self.input_files = glob.glob(self.data_dir + '/*.dat')
        elif input_file:
            self.input_files = glob.glob(self.input_file)
        else:
            self.input_files = []
            self.error_msg('No input files provided.')

        logging.debug(self.input_files)
        self.num_of_files = len(self.input_files)

        if self.num_of_files < 1:
            self.error_msg('No data files found for ingestion')

        if import_dir:
            self.import_dir = import_dir
        else:
            self.import_dir = 'parameter'
            
        if not os.path.isdir('{}/{}'.format(self.ares_import, self.import_dir)):
            self.error_msg('Location for importing input files {0} does not exist'
                           .format(self.import_dir))

    def error_msg(self, msg):
        if self.batch_mode:
            logging.error(msg)
        else:
            logging.fatal(msg)
            os._exit(1)

    def set_predef_type_patterns(self, patdict):
        '''
        Use as patterns the ones provided by the user
        '''
        try:
            self.ares_data_types = patdict
            self.compile_patterns()
            self.hasCompiledPatterns = True
        except:
            self.error_msg('Problem while compiling user provided patterns')

    def compile_patterns(self):
        '''
        Compile patterns used to define file data type
        '''
        for typ, data in self.ares_data_types.items():
            self.ares_data_types[typ]['re'] = re.compile(data['re'])

    def tail(self, f, lines=1, _buffer=4098):
        '''
        Tail a file and get X lines from the end
        :param f: File handler
        :param lines: number of lines to take from the end
        :param _buffer: Buffer size
        :return: lines from the end of the file
        '''
        # place holder for the lines found
        lines_found = []

        # block counter will be multiplied by buffer to get the block size from the end
        block_counter = -1

        # loop until we find X lines
        while len(lines_found) < lines:
            try:
                f.seek(block_counter * _buffer, os.SEEK_END)
            except IOError:  # either file is too small, or too many lines requested
                f.seek(0)
                lines_found = f.readlines()
                break

            lines_found = f.readlines()

            # decrement the block counter to get the next X bytes
            block_counter -= 1

        return lines_found[-lines:]

    def wait_until_import_is_successful(self):
        '''
        Continuously monitor ARES server log file to determine whether the import
        was successful
        :return:
        '''
        time.sleep(3)
        result = False
        end_monitor = False
        with open(self.admin_server_log, 'r') as f:
            while not end_monitor:
                # Time delay (give some time to do the import)
                time.sleep(1)

                # Check last line
                last_2_lines = self.tail(f, lines = 2)
                line1 = last_2_lines[0]
                line2 = last_2_lines[1]
                #print ">>> {0}\n>>> {1}\n".format(line1,line2)
                if re.search(r' - Finished importing', line2):
                    if re.search(r' - Import time:', line1):
                        result = True
                        end_monitor = True
                    if re.search(r' - Import of task .* failed', line1):
                        result = False
                        end_monitor = True
                    if re.search(r'_PARAM_DEF_', line2):
                        result = True
                        end_monitor = True

                # Otherwise, keep monitoring

        return result

    def import_descriptions(self):
        '''
        Makes an import of a CSV description file.
        It is assumed that the 'paramdef' part in the import folder name must be
        placed instead of the 'parameter'.
        '''
        if not self.import_dir:
            self.error_msg('Import folder for description file is missing!')

        fimport_dir = self.import_dir
        fimport_dir = fimport_dir.replace('parameter', 'paramdef')
        logging.info('Import folder for description file is {0}'.format(fimport_dir))

        fname = self.desc_file
        logging.info('Preparing import of description file: {0}'
                     .format(fname))

        import_dir = self.ares_import + '/' + fimport_dir
        logging.info('Data type: {0} (folder: {1})'.format('DESC_FILE',import_dir))

        # Copy def file to import folder
        copy(fname, import_dir)

        if not self.wait_until_import_is_successful():
            self.error_msg('Import of description file failed. Exiting.')

        #self.import_dir = 'parameter/' + self.import_dir

    def update_stats_on_result(self, result):
        '''
        Updates number of files
        '''
        if result:
            self.num_of_imported_files += 1
            logging.info('Data file imported successfully')
        else:
            self.num_of_failed_files += 1
            logging.warn('Data file importing failed!')

    def do_import_files(self):
        '''
        Loop over input files, to import each of them sequentally
        '''

        # Main loop on files
        for i, fname in enumerate(self.input_files):
            logging.info('Preparing import of file {0} of {1}: {2}'
                         .format(i + 1, self.num_of_files, fname))

            # Detect data type
            ftype = None
            fimport_dir = ''
            if self.import_dir:
                ftype = '<assumed from specified folder>'
                fimport_dir = self.import_dir
            else:
                if self.data_type:
                    ftype = self.data_type
                    fimport_dir = self.ares_data_types[ftype]['dir']
                else:
                    for typ, typ_info in self.ares_data_types.items():
                        rx = typ_info['re']
                        if rx.match(os.path.basename(fname)):
                            ftype = typ
                            fimport_dir = typ_info['dir']
                            break

            if not ftype:
                logging.warn('Unidentified data file type. Failed import.')
                self.num_of_failed_files += 1
                continue

            import_dir = self.ares_import + "/" + fimport_dir
            logging.info('Data type: {0} (folder: {1})'.format(ftype,import_dir))

            # Copy data file to import folder
            copy(fname, import_dir)

            # Wait for the result
            import_result = self.wait_until_import_is_successful()
            self.update_stats_on_result(import_result)

    def run_import(self):
        '''
        Execute import, for one single file or an entire directory, if specified
        '''
        if self.num_of_files < 1:
            return

        if not self.hasCompiledPatterns:
            logging.error('No patterns file was found nor patterns were provided by the user')
            #os._exit(1)

        #self.compile_patterns()

        logging.info('Import process starting')
        logging.info('-'*60)

        self.do_import_files()

        if self.desc_file:
            logging.info('-'*60)
            logging.info('Importing parameter descriptions . . .')
            self.import_descriptions()

        logging.info('-'*60)
        logging.info('Import process completed.')
        logging.info('{0} of {1} files successfully imported.'
                     .format(self.num_of_imported_files, self.num_of_files))
        if self.num_of_failed_files > 0:
            logging.warn('{0} of {1} files import failed.'
                         .format(self.num_of_failed_files, self.num_of_files))
        logging.info('-'*60)
        logging.info('Done.')


def main():
    '''
    Main processor program
    '''
    importer = Importer()


if __name__ == "__main__":
    main()
