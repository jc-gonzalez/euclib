#!/usr/bin/python
# -*- coding: utf-8 -*-
'''fnamespec

Classes to handle File Naming Conventions for Euclid files'''

from astropy.io import fits
from enum import Enum
from pprint import pprint

import os, sys
import re
import json

import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


#----------------------------------------------------------------------------
# Enum FileFormat: Internal format of file
#----------------------------------------------------------------------------
class FileFormat(Enum):
    UNKNOWN = 0
    FITS = 1
    JSON = 2
    LOG = 3
    CSV = 4
    HDF = 5
    DAT = 6

    def __str__(self):
        return '{0}'.format(self.name)

#----------------------------------------------------------------------------
# Enum ObsMode: Observation Mode
#----------------------------------------------------------------------------
class ObsMode(Enum):
    Unknown = '?'
    Wide = 'W'
    Deep = 'D'
    Calib = 'C'

    def getObsMode(self, val):
        return self._value2member_map_[val]
    def __str__(self):
        return '{0}'.format(self.name)

#----------------------------------------------------------------------------
# Enum ProcessingFunction: Type of image according to its size
#----------------------------------------------------------------------------
class ProcessingFunction(Enum):
    UNK =  0  # Unknown
    SIM =  1  # Simulated Euclid data
    EXT =  2  # External source data from ground based Observatoryessing
    VIS =  3  # VIS proc. function: calibrated images/exposures, stacks, masks, catalog
    NIR =  4  # NIR proc. function: calibrated images/exposures, stacks, masks, catalog
    SIR =  5  # SIR proc. function: calibrated exposures and masks, 1D/2D spectra, combined spectra
    SPE =  6  # SPE proc. function: spectrometric redshift extraction, emission lines, extraction lines
    SHE =  7  # SHE proc. function: galaxy shape, shear values extraction
    PHZ =  8  # PHZ proc. function: photometric redshift estimation, PDF
    LE3 =  9  # LE3 proc. function
    LE1 = 10  # Decompressed scientific data
    DQC = 11  # Data Quality Check
    CAL = 12  # Calibration processing function
    TRD = 13  # Transient detection
    SOC = 14  # Raw TM or HKTM
    QLA = 15  # SOC QLA Generated reports/logs
    HMS = 16  # SOC HMS Generated reports/logs
    ESS = 17  # SOC HMS Generated reports/logs
    SCS = 18  # SOC HMS Generated reports/logs

    def __str__(self):
        return '{0}'.format(self.name)

#----------------------------------------------------------------------------
# Class ProductMetadata
#----------------------------------------------------------------------------
class ProductMetadata:
    '''
    Class ProductMetadata

    Encapsulated the metadata information from a given product
    '''
    logger = logging.getLogger(__name__ + '.ProductMetadata') #__class__.__name__)
    if not logger.handlers: logger.addHandler(logging.NullHandler())

    FileNameSpecRE = r"(?P<mission>[A-Z]{3,3})_(?P<procfunc>[A-Z0-9]{3,3})_(?P<instance>[^_]+)_" + \
                     r"(?P<date>[0-9]+T[\.0-9]+Z)[_]*(?P<version>[0-9]*\.*[0-9]*)"
    SpectralBands = 'UBVRIJHKLMNQGZY'
    Creators = "-NIR-SIR-VIS-"
    DataTypes = "-CAT-TRANS-STACK-MASK-MAP-PSF-SPE1D-MAP2DCOR-TIPS-"

    def __init__(self, file=None):
        '''
        Instance initialization method
        '''
        ProductMetadata.logger.info('Instance initialized')
        self.reset()
        self.re = re.compile(ProductMetadata.FileNameSpecRE)
        if file:
            self.parse(file)

    def reset(self):
        '''
        Initializes the metadata structure
        :return: -
        '''
        self.meta = {
            "mission": None,
            "creator": None,
            "proc_func": None,
            "obs_id": None,
            "params": None,
            "signature": None,
            "instrument": None,
            "spectral_band": None,
            "obs_mode": None,
            "exposure": None,
            "type": None,
            "data_type": None,
            "id": None,
            "status": None,
            "size": None,
            "format": None,
            "version": None,
            "start_time": None,
            "end_time": None,
            "url": None,
            "additional": None,
            "meta": None
        }

    def parse(self, file):
        '''
        Parses the file name according to the Euclid File Naming Conventions,
        and fills the metadata structure
        :param file: the input file name
        :return: the metadata structure
        '''
        self.reset()
        fileinit, file_ext = os.path.splitext(file)
        file_path = os.path.dirname(fileinit)
        file_bname = os.path.basename(fileinit)
        self.meta['id'] =  file_bname
        self.meta['fileinfo'] = {'path': file_path,
                                 'base': file_bname,
                                 'name': file_bname + file_ext,
                                 'ext': file_ext[1:]}
        self.meta['format'] = self.genProdFormat()

        self.match = self.re.match(self.meta['fileinfo']['name'])

        if not self.match: return None

        self.meta['mission'] = self.match.group('mission')
        self.meta['proc_func'] = self.match.group('procfunc')
        self.meta['creator'] = self.match.group('procfunc')
        self.meta['instance'] = self.match.group('instance')
        self.meta['start_date'] = self.match.group('date')
        self.meta['version'] = self.match.group('version')

        self.parseInstance()

        # Gather metadata for structured data files that contain it
        self.meta['exists'] = os.path.isfile(file)
        if self.meta['exists']:
            self.retrieveInternalMetadata(file)
        else:
            self.logger.warning('File {} does not exist in the current file system'.format(file))
            #print('FILE {} DOES NOT EXIST!'.format(file))
            pass

        return self.meta

    def metadata(self):
        '''
        Returns the metadata structure
        :return:
        '''
        return self.meta

    def genProdFormat(self):
        '''
        Generate the product internal format identifier
        :return: FileFormat identifier
        '''
        ext = self.meta['fileinfo']['ext'].upper()
        try:
            return FileFormat[ext]
        except:
            self.logger.warning('Unknown extension ({}) / internal file format'.format(ext))
            return FileFormat.UNKNOWN

    def parseInstance(self):
        '''
        Parse the 'instance' group in the file name, with the obs.id., data type,
        spectral band, exposure, etc.
        :return: -
        '''
        insTokens = self.meta['instance'].split('-')
        for token in insTokens:
            if len(token) == 1:
                if token in ProductMetadata.SpectralBands:
                    self.meta['spectral_band'] = token
                elif token.isnumeric():
                    self.meta['exposure'] = int(token)
                else:
                    try:
                        self.meta['obs_mode'] = ObsMode._value2member_map_[token]
                    except:
                        self.logger.warning('Could not identify the token "{}"'.format(token))
            elif token.isnumeric():
                self.meta["obs_id"] = token
            elif '-' + token + '-' in ProductMetadata.Creators:
                self.meta["creator"] = token
            elif '-' + token + '-' in ProductMetadata.DataTypes:
                self.meta["data_type"] = token
            else:
                ad = self.meta['additional']
                if not ad:
                    self.meta['additional'] = token
                else:
                    self.meta['additional'] = '-'.join([ad, token])

        self.meta["type"] = self.meta["proc_func"] + \
                            (("_" + self.meta["creator"])
                              if (self.meta["proc_func"] != self.meta["creator"]) else "")

    def retrieveInternalMetadata(self, file):
        '''
        Takes internal metadata information (FITS keywords, Header sections in JSON, etc.),
        and incorporates them to the metadata structure
        :param file: the input file name
        :return: -
        '''
        if self.meta['format'] == FileFormat.FITS:
            with fits.open(file) as hdul:
                startHdu = 1 if len(hdul) > 1 else 0
                self.meta['meta'] = {'start_hdu': startHdu,
                                     'num_extensions': len(hdul) - startHdu,
                                     'dims': [hdu.data.shape for hdu in hdul[startHdu:]],
                                     'headers': [hdu.header for hdu in hdul]}
        elif self.meta['format'] == FileFormat.JSON:
            with open(file) as jfp:
                jData = json.load(jfp)
                jKeys = jData.keys()
                for h in ['header', 'Header', 'HEADER',
                          'metadata', 'Metadata', 'METADATA']:
                    if h in jKeys:  self.meta['meta'] = jData[h]
        # elif self.meta['format'] == FileFormat.LOG:
        #     pass
        # elif self.meta['format'] == FileFormat.CSV:
        #     pass
        # elif self.meta['format'] == FileFormat.HDF:
        #     pass
        # elif self.meta['format'] == FileFormat.DAT:
        #     pass
        else:
            logger.warning('File {} does not contain internal metadata'.format(file))
            pass
        

def main():
    '''
    Main processor program
    '''

    fileNames = [
       #'EUC_LE1_NIR-00034_20191212T101212.000000Z_03.04.fits',
       #'EUC_LE1_SIR-00034_20191212T101212.000000Z_03.04.fits',
       #'EUC_LE1_VIS-00034_20191212T101212.000000Z_03.04.fits',
       #'EUC_MER_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_MER_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_MER_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_MER_TRANS-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-12000-1-Y_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-12000-1-Y_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-12000-4-H_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-12000-4-H_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_C-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-12000-2-J_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-CALIB-12000-2-J_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-CALIB-12000-2-J_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_D-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_TRANS-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-12000-1-Y_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-CALIB-12000-1-H_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-CALIB-12000-1-H_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_NIR_W-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_PHZ_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_PHZ_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_SHE_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_SHE_CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIM_NIP-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIM_TIPS-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIM_VIS-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_C-12000-1_20211212T101212.0Z_0000004.03.fits',
       #'EUC_SIR_C-12000-1_20211212T101212.0Z_0000004.03.fits',
       #'EUC_SIR_D-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-CALIB-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-CALIB-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-SPE1D-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-SPE1D-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-SPE2D-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-SPE2D-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_D-SPEX-12000-2_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-CALIB-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-CALIB-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-SPE1D-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-SPE1D-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-SPE2D-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-SPE2D-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_SIR_W-SPEX-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_C-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_C-CALIB-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_C-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_D-12000-4_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_D-CALIB-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_D-CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_D-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_D-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_TRANS-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_W-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_W-CALIB-12000-1_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_W-CAT-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_W-PSF-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_VIS_W-STACK-12000_20211212T101212.000000Z_04.03.fits',
       #'EUC_MER_PSF-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_PSF-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_REBINNED-PSF-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_REBINNED-PSF-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_CONV-KERNEL-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_CONV-KERNEL-NIRH_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_TRANS-KERNEL-VIS-KIDU_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_TRANS-KERNEL-NIRH-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-FRAME-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-FRAME-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-STACK-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-STACK-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGMOD-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGMOD-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_MOSAIC-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_MOSAIC-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-MOSAIC-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-MOSAIC-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_PSFMATCHED-MOSAIC-VIS-NIRY_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_PSFMATCHED-MOSAIC-NIRH-DESG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DET-MOSAIC-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DET-MOSAIC-VIS-NIR_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DEBL-MOSAIC-VIS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DEBL-MOSAIC-VIS-NIR_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DET-SEGMAP_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DEBL-SEGMAP_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_FINAL-CAT_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_DEBL-CAT_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_APHOT-CAT_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_MOSAIC-VIS-FLAG_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_BGSUB-MOSAIC-DESG-RMS_20161019T103022.500000Z_00.01.fits',
       #'EUC_MER_LIST-VIS_20161019T103022.500000Z_00.01.json',
       #'EUC_MER_LIST-NIRJ_20161019T103022.500000Z_00.01.json',
       #'EUC_QLA_SIM-VIS-00928-1-W-Short_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02354-1-W-FlatNoCTI_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02361-1-W-BiasDrift_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00928-1-W-Short_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02354-1-W-FlatNoCTI_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02363-1-W-TrapPump_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00929-1-W-FlatHighRON_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02357-1-W-Flat_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02364-1-W-NominalFullFPA_20250520T063201.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00929-1-W-FlatHighRON_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02357-1-W-Flat_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02366-1-W-ChrInj_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00931-1-W-BiasHighBias_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02358-1-W-FlatInconsistent_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02367-1-W-Nominal_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00931-1-W-BiasHighBias_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02358-1-W-FlatInconsistent_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02368-1-W-BiasUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00932-1-W-NominalWrongWCS_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02359-1-W-ChrInjUnOvFlow_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02369-1-W-ChrInjHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00932-1-W-NominalWrongWCS_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02359-1-W-ChrInjUnOvFlow_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02370-1-W-ShortHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00933-1-W-LinearHighBias_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02360-1-W-ChrInjWrongLevel_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02371-1-W-TrapPumpHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00933-1-W-LinearHighBias_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02360-1-W-ChrInjWrongLevel_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02372-1-W-Bias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00934-1-W-NominalLowGain_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02361-1-W-BiasDrift_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02373-1-W-FlatPRNU_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00934-1-W-NominalLowGain_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02361-1-W-BiasDrift_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02374-1-W-DarkHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00935-1-W-FlatLowGain_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02363-1-W-TrapPump_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_VIS-02375-1-W-NominalUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00935-1-W-FlatLowGain_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02363-1-W-TrapPump_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_VIS-02376-1-W-ShortGauss0.25_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00936-1-W-Flat0.1CTI_20240520T063000.0Z_01.00.json',
       #'EUC_QLA_SIM-VIS-02364-1-W-NominalFullFPA_20250520T063201.0Z_01.00.json',
       #'EUC_SIM_VIS-02378-1-W-DarkNoCR_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00936-1-W-Flat0.1CTI_20240520T063000.0Z_01.00.log',
       #'EUC_QLA_SIM-VIS-02364-1-W-NominalFullFPA_20250520T063201.0Z_01.00.log',
       #'EUC_SIM_VIS-02379-1-W-DarkHighCR_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00937-1-W-Manual_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00022-1-W-NOMINAL_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02380-1-W-ChrInjWrongPattern_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00937-1-W-Manual_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00026-1-W-NOMINAL_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02381-1-W-LinearUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00939-1-W-ShortNoSources_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00065-3-W-DARK_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02382-1-W-FlatUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00939-1-W-ShortNoSources_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00075-3-W-DARK_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02383-1-W-FlatHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00940-1-W-LinearHighRON_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00078-2-W-FLAT_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02384-1-W-DarkHighDark_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00940-1-W-LinearHighRON_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00079-3-W-DARK_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02385-1-W-Flat900_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00941-1-W-Dark_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00083-1-W-NOMINAL_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02386-1-W-ShortWrongWCS_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00941-1-W-Dark_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00090-2-W-FLAT_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02388-1-W-NominalHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00942-1-W-NominalGauss0.1_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00106-2-W-FLAT_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02389-1-W-NominalHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00942-1-W-NominalGauss0.1_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00113-1-W-NOMINAL_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02392-1-W-FlatLowResp_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00943-1-W-ShortHighRON_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00114-1-W-NOMINAL_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02393-1-W-NominalNoSources_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00943-1-W-ShortHighRON_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00135-3-W-DARK_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02394-1-W-ChrInjHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00944-1-W-BiasHighRON_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00145-3-W-DARK_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02396-1-W-ChrInjCTI_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00944-1-W-BiasHighRON_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00148-2-W-FLAT_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02397-1-W-DarkUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00945-1-W-ShortUnOvFlow_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00149-3-W-DARK_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02399-1-W-BiasHotCol_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00945-1-W-ShortUnOvFlow_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00153-1-W-NOMINAL_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02400-1-W-Short_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00947-1-W-DarkHighBias_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00160-2-W-FLAT_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02401-1-W-FlatHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00947-1-W-DarkHighBias_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00176-2-W-FLAT_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02403-1-W-BiasHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00948-1-W-ShortGauss0.1_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00183-1-W-NOMINAL_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02404-1-W-NominalWrongWCS_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00948-1-W-ShortGauss0.1_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00184-1-W-NOMINAL_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02405-1-W-LinearHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00949-1-W-Linear_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00205-3-W-DARK_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02406-1-W-NominalLowGain_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00949-1-W-Linear_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00215-3-W-DARK_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02407-1-W-FlatLowGain_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00950-1-W-TrapPumpHighRON_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00218-2-W-FLAT_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02408-1-W-Flat0.1CTI_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00950-1-W-TrapPumpHighRON_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00219-3-W-DARK_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02409-1-W-Manual_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00951-1-W-TrapPumpUnOvFlow_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00223-1-W-NOMINAL_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02411-1-W-ShortNoSources_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00951-1-W-TrapPumpUnOvFlow_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00230-2-W-FLAT_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02412-1-W-LinearHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00952-1-W-FlatNoCTI_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00246-2-W-FLAT_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02413-1-W-Dark_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00952-1-W-FlatNoCTI_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00253-1-W-NOMINAL_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02414-1-W-NominalGauss0.1_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00955-1-W-Flat_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00254-1-W-NOMINAL_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02415-1-W-ShortHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00955-1-W-Flat_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00275-3-W-DARK_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02416-1-W-BiasHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00956-1-W-FlatInconsistent_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00285-3-W-DARK_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02417-1-W-ShortUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00956-1-W-FlatInconsistent_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00288-2-W-FLAT_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02419-1-W-DarkHighBias_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00957-1-W-ChrInjUnOvFlow_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00289-3-W-DARK_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02420-1-W-ShortGauss0.1_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00957-1-W-ChrInjUnOvFlow_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00293-1-W-NOMINAL_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02421-1-W-Linear_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00958-1-W-ChrInjWrongLevel_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00300-2-W-FLAT_20170525T122745.733Z_01.00.fits',
       #'EUC_SIM_VIS-02422-1-W-TrapPumpHighRON_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00958-1-W-ChrInjWrongLevel_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00316-2-W-FLAT_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02423-1-W-TrapPumpUnOvFlow_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00959-1-W-BiasDrift_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00323-1-W-NOMINAL_20170525T122804.242Z_01.00.fits',
       #'EUC_SIM_VIS-02424-1-W-FlatNoCTI_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00959-1-W-BiasDrift_20240520T063000.0Z_01.00.log',
       #'EUC_SIM_NIR-00324-1-W-NOMINAL_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02427-1-W-Flat_20240520T063000.0Z_01.00.fits',
       #'EUC_QLA_SIM-VIS-00961-1-W-TrapPump_20240520T063000.0Z_01.00.json',
       #'EUC_SIM_NIR-00345-3-W-DARK_20170525T122751.138Z_01.00.fits',
       #'EUC_SIM_VIS-02428-1-W-FlatInconsistent_20240520T063000.0Z_01.00.fits',
       #'/Users/jcgonzalez/Test_Data/AOCS_1Realization_Nom.fits',
       #'/Users/jcgonzalez/Test_Data/AOCS_1Realization_WC.fits',
       #'/Users/jcgonzalez/Test_Data/AOCS_1Realization_WC_10x.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_NIR-12345-1-W-Dark_20240520T063201.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_NIR-12346-1-W-Flat_20240520T063202.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_SIR-12346-1-W-Flat_20240520T063202.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-11140-1-W-ChrInjFromLab_20180207T121254.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-11160-1-W-ChrInjFromLab_20180207T130614.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-12345-1-W-Nominal_20240520T063201.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-12346-1-W-NominalLowSatLevel_20240520T063202.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-12351-1-C-Dark_20240520T063210.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-12352-1-D-DarkNoCR_20240520T063211.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_LE1_VIS-12353-1-W-DarkHigh_20240520T063212.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_NIR-12347-1-W-Linearity_20240520T063203.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_NIR-12348-1-W-Nominal_20240520T063204.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_NIR-34080-4-W-Nominal_20250520T063204.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_SIR-12348-1-W-Nominal_20240520T063204.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_SIR-34080-1-W-Nominal_20250520T063201.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12347-1-W-NominalHighBias_20240520T063203.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12348-1-W-NominalHighGain_20240520T063204.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12349-1-W-NominalHighRON_20240520T063205.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12350-1-W-TrapPump_20240520T063206.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12350-2-W-Linearity_20240520T063207.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12350-3-W-ChrInj_20240520T063208.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12350-4-W-Short_20240520T063209.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12354-1-W-Bias_20240520T063213.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12355-1-W-BiasDrift_20240520T063214.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12356-1-C-Flat_20240520T063215.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12357-1-D-FlatNoCTI_20240520T063216.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-12358-1-W-FlatVarGain_20240520T063217.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SIM_VIS-34080-1-W-Nominal_20250520T063201.0Z.fits',
        '/Users/jcgonzalez/Test_Data/EUC_SOC_NIR-12359-1-W-L0Test_20240520T063218.0Z.hdf',
        '/Users/jcgonzalez/Test_Data/EUC_SOC_VIS-12360-1-W-L0Test_20240520T063219.0Z.fits'
    ]

    i = 1
    firstTime = True
    prodMeta = ProductMetadata()
    maxLen = max([len(x) for x in fileNames])

    for f in fileNames:

        print('{0:3d} - {1:<{size}}:  '.format(i, f, size=maxLen), end='')

        meta = prodMeta.parse(file=f)
        if meta:
            #print(meta)
            plain_meta = meta
            plain_meta.pop('fileinfo')
            meta_meta = plain_meta.pop('meta')
            if firstTime:
                hdrs = plain_meta.keys()
                print(''.join(['{:>15}'.format(x) for x in hdrs]))
                firstTime = False
            values = [('{:>15}'.format(meta[x] if meta[x] else '')) for x in hdrs]
            values15 = [x[:15] for x in values]
            print(' | '.join(values15))
            if meta_meta:
                pprint(meta_meta)

        i = i + 1


if __name__ == "__main__":
    main()
