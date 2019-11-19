#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
raw2vis.py

RAW to VIS Conversion class
"""
#----------------------------------------------------------------------

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

# System
import os
import sys
import logging

import numpy as np

from astropy.io import fits
#from pprint import pprint
from struct import Struct
from enum import IntEnum

from le1_vis import RAWVISHeader, RAWVISHeader_prev, RAWVISHeader_old, \
                    RAWVISSciDataPacket, \
                    VISSize, read_4_byte_word


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

class InputType(IntEnum):
    RAW = 0,       # ICD 4.0 draft 9
    RAW_PREV = 1,  # ICD 4.0 draft 9 almost
    RAW_OLD = 2,   # ICD 3.4
    LE1 = 3,
    UNKNOWN = -1

    @staticmethod
    def inputType(s):
        """
        Convert a string to a InputType, if possible
        :param s: the string
        :return: the input type enumerator
        """
        return max([y if s in x else InputType.UNKNOWN for x,y in Str2InputType])

Str2InputType = [(['raw', 'icd-4.0d9'], InputType.RAW),
                 (['raw-prev', 'icd-4.0d8'], InputType.RAW_PREV),
                 (['raw-old', 'icd-3.4'], InputType.RAW_OLD),
                 (['le1'], InputType.LE1)]
InputTypeStrChoices = [x for sl,t in Str2InputType for x in sl]

class OutputType(IntEnum):
    LE1 = 0,
    QUAD = 1,
    FPA = 2,
    FULL_FPA = 3,
    UNKNOWN = -1

    @staticmethod
    def outputType(s):
        """
        Convert a string to a OutputType, if possible
        :param s: the string
        :return: the output type enumerator
        """
        return max([y if s in x else OutputType.UNKNOWN for x,y in Str2OutputType])

Str2OutputType = [(['le1'], OutputType.LE1),
                  (['quad'], OutputType.QUAD),
                  (['fpa'], OutputType.FPA),
                  (['fullfpa'], OutputType.FULL_FPA)]
OutputTypeStrChoices = [x for sl,t in Str2OutputType for x in sl]


class RAW_to_VIS_Processor:
    """
    Class RAW_to_VIS_Processor

    VIS RAW Data File to LE1 VIS Processor
    """
    def __init__(self, args):
        """
        Initialization method
        """
        self.npackets_roe = []
        self.nbytes = 0
        self.npackets = 0
        self.npackets_hdr = 0

        self.images = []
        self.ccd_number = []

        self.row_unpacker_fmt = '{}H'.format(VISSize.COLS_HALF)
        self.row_unpacker = Struct(self.row_unpacker_fmt)

        self.input_type = args.input_type
        self.output_type = args.output_type

        self.input_file = args.input_file
        self.output_dir = args.output_dir

        def ccdq_to_extnum(b, n, q):
            return (((b - 1) * 24 + (6 - n) * 4) + q +
                    (0 if n >= 4 else (2 if q <= 2 else -2)))
        self.ext2quad = {ccdq_to_extnum(b, n, q) : (b, n, q) \
                         for b in range(1,7) \
                         for n in range(1,7) \
                         for q in range(1,5)}

        #logger.info('{}'.format(self.ext2quad))

    def create_internal_structures(self):
        """
        Create header and packet structures, depending on the
        :return:
        """
        self.visHdr = [RAWVISHeader,\
                       RAWVISHeader_prev,
                       RAWVISHeader_old][int(self.input_type)]()
        self.visSciPck = RAWVISSciDataPacket()

    def process_input(self):
        """
        Run the processing of the input file
        :return:
        """
        n = 0
        nn = []

        with open(self.input_file, 'rb') as fh:
            while True:
                word = read_4_byte_word(fh)

                if word == RAWVISHeader.InitialMark:
                    self.npackets_roe.append(self.npackets)
                    nn.append(n)
                    n = 0
                    # Header packet
                    if self.visHdr.read(fh):
                        logger.debug(self.visHdr.info())
                        self.npackets_hdr = self.npackets_hdr + 1
                        self.nbytes = self.nbytes + self.visHdr.size
                    else:
                        logger.error('Cannot read file header.')
                        return

                elif word == RAWVISSciDataPacket.InitialMark:
                    # Science packet
                    if not self.visSciPck.read(fh): break

                    n = n + 1
                    self.npackets = self.npackets + 1
                    self.nbytes = self.nbytes + self.visSciPck.size

                    # Put data into image
                    ccdn = self.visSciPck.ccdId.ccd_id
                    if ccdn >= len(self.images):
                        logger.info(f'Reading data for CCD {ccdn}')
                        self.images.append(np.zeros((VISSize.ROWS, VISSize.COLS), dtype=int))
                        self.ccd_number.append(ccdn + 1)

                    row = self.visSciPck.ccdId.row
                    col = self.visSciPck.ccdId.col
                    dataRow = np.array(self.row_unpacker.unpack(self.visSciPck.data.binstr))

                    if col == 0:
                        if row < VISSize.ROWS_HALF:
                            self.images[ccdn][row,0:VISSize.COLS_HALF] = dataRow # Q1: E
                        else:
                            self.images[ccdn][row,0:VISSize.COLS_HALF] = dataRow # Q4: H
                    else:
                        if row < VISSize.ROWS_HALF:
                            self.images[ccdn][row,-1:-VISSize.COLS_HALF-1:-1] = dataRow # Q2: F
                        else:
                            self.images[ccdn][row,-1:-VISSize.COLS_HALF-1:-1] = dataRow # Q3: G
                else:
                    if word != -1:
                        logger.debug(f'Read from file: 0x{word:08X}')
                    break

        nn.append(n)
        self.npackets_roe.append(self.npackets)
        self.npackets_per_roe = [x-y for x,y in zip(self.npackets_roe[1:],
                                                    self.npackets_roe[:-1])]

        logger.info(f'{self.nbytes} bytes')
        logger.info(f'{self.npackets_hdr} header packets')
        logger.info(f'{self.npackets} science packets')
        logger.info('Sci.Packets per ROE: {}'.\
                    format(', '.\
                           join(['{}:{}'.format(i+1, self.npackets_per_roe[i]) \
                                 for i in range(0, len(self.npackets_per_roe))])))

    def generate_output(self):
        """
        Run the processing of the input file
        :return:
        """

        # Primary HDU with general info
        ## hdu0 = fits.PrimaryHDU()
        ## hdul = fits.HDUList([hdu0])
        ##
        ## # Then, an extension with each image, without any actual order
        ## for ccdn,img in zip(ccd_number, images):
        ##     hdu = fits.ImageHDU(img)
        ##     hdu.header['CCD_NUM'] = ccdn
        ##     hdul.append(hdu)
        ##
        ## hdul.writeto('test.fits', overwrite=True)

        if self.output_type == OutputType.LE1:
            le1file = os.path.join(self.output_dir,
                                   os.path.basename(self.input_file) + '.fits')

            hdu0 = fits.PrimaryHDU()
            hdu0.writeto(le1file, overwrite=True)

            for extn in range(1,145):
                (b, n, q) = self.ext2quad[extn]
                ccdn = (b - 1) * 6 + n - 1
                qlet = 'EFGH'[q-1:q]
                img = self.images[ccdn]
                logger.debug(f'({b}, {n}, {q}) => {extn} => {ccdn + 1}.{qlet}')
                if q == 1: # E
                    hdu = fits.ImageHDU(img[0:VISSize.ROWS_HALF,0:VISSize.COLS_HALF])
                elif q == 2: # F
                    hdu = fits.ImageHDU(img[0:VISSize.ROWS_HALF,-1:-VISSize.COLS_HALF-1:-1])
                elif q == 3: # G
                    hdu = fits.ImageHDU(img[-1:-VISSize.ROWS_HALF-1:-1,-1:VISSize.COLS_HALF-1:-1])
                else: # H
                    hdu = fits.ImageHDU(img[-1:-VISSize.ROWS_HALF-1:-1,0:VISSize.COLS_HALF])
                hdu.header['EXTNAME'] = f'CCD_{b}-{n}.{q}'
                hdu.header['CCDNUM'] = ccdn
                hdu.header['QUADRANT'] = qlet
                fits.append(le1file, hdu.data, hdu.header)

        elif self.output_type == OutputType.QUAD:
            hdu0 = fits.PrimaryHDU()
            hdul = fits.HDUList([hdu0])
            for ccdn,img in zip(self.ccd_number, self.images):
                # E
                hdu = fits.ImageHDU(img[0:VISSize.ROWS_HALF,0:VISSize.COLS_HALF])
                hdu.header['CCD_NUM'] = ccdn
                hdu.header['QUADRANT'] = 'E'
                hdul.append(hdu)

                # F
                hdu = fits.ImageHDU(img[0:VISSize.ROWS_HALF,-1:-VISSize.COLS_HALF-1:-1])
                hdu.header['CCD_NUM'] = ccdn
                hdu.header['QUADRANT'] = 'F'
                hdul.append(hdu)

                # G
                hdu = fits.ImageHDU(img[-1:-VISSize.ROWS_HALF-1:-1,-1:VISSize.COLS_HALF-1:-1])
                hdu.header['CCD_NUM'] = ccdn
                hdu.header['QUADRANT'] = 'G'
                hdul.append(hdu)

                # H
                hdu = fits.ImageHDU(img[-1:-VISSize.ROWS_HALF-1:-1,0:VISSize.COLS_HALF])
                hdu.header['CCD_NUM'] = ccdn
                hdu.header['QUADRANT'] = 'H'
                hdul.append(hdu)

            hdul.writeto(os.path.join(self.output_dir,
                                      os.path.basename(self.input_file) + '.fits'),
                         overwrite=True)

        elif self.output_type == OutputType.FPA:
            hdu0 = fits.PrimaryHDU()
            hdul = fits.HDUList([hdu0])
            for ccdn,img in zip(self.ccd_number, self.images):
                hdu = fits.ImageHDU(img)
                hdu.header['CCD_NUM'] = ccdn
                hdul.append(hdu)

            hdul.writeto(os.path.join(self.output_dir,
                                      os.path.basename(self.input_file) + '.fits'),
                         overwrite=True)

        elif self.output_type == OutputType.FULL_FPA:
            logger.warn('Full-FPA output format still not supported')

        else:
            logger.error('No output will be produced')

    def run(self):
        """
        Run the processing of the input file and the generation of the output file(s)
        :return:
        """
        self.create_internal_structures()
        self.process_input()
        self.generate_output()


if __name__ == '__main__':
    pass
