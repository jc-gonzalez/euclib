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

import ricecomp
#import risotto

from astropy.io import fits
from pprint import pprint
from struct import Struct
from enum import IntEnum

from le1_vis import RAWVISHeader, RAWVISHeader_prev, RAWVISHeader_old, \
                    RAWVISSciDataPacket, \
                    VISSize, read_4_byte_word
from le1_base import ComprType
from array import array

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

    def defineQuadrant(self, row, col):
        """
        Sets the instance flags according to the quadrant where (row,col) is located
        :param row: The row
        :param col: The column
        :return: -
        """
        self.isQuadE = self.isQuadF = self.isQuadG = self.isQuadH = False
        if row < VISSize.ROWS_HALF:
            self.isQuadE = col < VISSize.COLS_HALF
            self.isQuadF = not self.isQuadE
        else:
            self.isQuadH = col < VISSize.COLS_HALF
            self.isQuadG = not self.isQuadH
        self.isQuadEorF = self.isQuadE or self.isQuadF
        self.isQuadGorH = self.isQuadG or self.isQuadH
        self.isQuadEorH = self.isQuadE or self.isQuadH
        self.isQuadForG = self.isQuadF or self.isQuadG

    def create_internal_structures(self):
        """
        Create header and packet structures, depending on the
        :return:
        """
        self.visHdr = [RAWVISHeader,\
                       RAWVISHeader_prev,
                       RAWVISHeader_old][int(self.input_type)]()
        self.visSciPck = RAWVISSciDataPacket()

    def uncompressData(self, bindata):
        """
        Unpack data from file and uncompress is (121)
        :param bindata: The data obtained from the input file
        :return: The uncompressed data
        """
        rawdata = np.frombuffer(bindata, dtype=np.uint8)
        #return np.linspace(0, VISSize.COLS_HALF, VISSize.COLS_HALF, dtype=np.uint16)
        try:
            # Try to decompress data
            print('rawdata: ',rawdata.shape)
            dataDec = np.zeros((VISSize.COLS_HALF,), dtype=np.uint16)
            dataDec = ricecomp.rdecomp(rawdata, np.uint16, VISSize.COLS_HALF, self.comprPrs)
            print('dataDec: ',dataDec.shape)
            #rowUpck = Struct('<{}H'.format(VISSize.COLS_HALF))
            #return np.array(rowUpck.unpack(dataDec), dtype=np.uint16)
            return dataDec
        except Exception as ee:
            print(ee, flush=True)
            #with open("bindata.bin", "wb") as fh:
            #    fh.write(bindata)
            #raise
            return dataDec

    def storeDataAtImageDirect(self, ccd, rw, cl, data):
        """
        Place the data of the row obtained into the final image
        :param ccdn: the CCD number
        :param rw: the row in the CCD
        :param cl: the column in the CCD
        :param data: the data (already uncompressed)
        :return:
        """
        if cl < VISSize.COLS_HALF:  # Quadrants E & H
            self.images[ccd][rw, 0:VISSize.COLS_HALF] = data[:]
        else:  # Quadrants F & G
            self.images[ccd][rw, -1:-VISSize.COLS_HALF - 1:-1] = data[:]

    def storeDataAtImageReordered(self, ccdn, row, col, dataRow):
        """
        Take the uncompressed data and reordered in the final image buffer
        :param ccdn: the CCD number
        :param row: the row in the CCD
        :param col: the column in the CCD
        :param dataRow: the data (already uncompressed)
        :return: -
        """
        self.is2RowArea = (-1 <= (row - VISSize.ROWS_HALF) <= 2)
        regions = (4 if not self.is2RowArea else 2)
        colblk = VISSize.COLS_HALF // regions

        dataRow = np.transpose(dataRow.reshape([i for i in reversed(dataRow.shape)]))

        idx = 0
        for ridx in range(0, regions):
            if self.isQuadEorH: # Quadrants E or H
                print("({},{}:{}) <- {}:{}, ".format(ridx, col, col + colblk, idx, idx + colblk), end='', flush=True)
                print("{}, {} ;".format(self.rowbuf[ridx, col:col + colblk].shape,
                                        dataRow[idx:idx + colblk].shape), end='', flush=True)
                self.rowbuf[ridx, col:col + colblk] = dataRow[idx:idx + colblk]
                idx = idx + colblk
            else: # Quadrants F or G
                print("({},{}:{}) <- {}:{}, ".format(ridx, col - VISSize.COLS_HALF - colblk + 1,
                                                     col - VISSize.COLS_HALF + 1, idx, idx + colblk), end='', flush=True)
                print("{}, {} ;".format(self.rowbuf[ridx, col - VISSize.COLS_HALF - colblk + 1:col - VISSize.COLS_HALF + 1].shape,
                                        dataRow[idx:idx + colblk].shape), end='', flush=True)
                self.rowbuf[ridx, col - VISSize.COLS_HALF - colblk + 1:col - VISSize.COLS_HALF + 1] = dataRow[idx:idx + colblk]
                idx = idx + colblk
        print('')

        self.storedBlocks = self.storedBlocks + 1

        if (self.storedBlocks == 4) or (self.storedBlocks == 2 and self.is2RowArea):
            self.storeBufferedDataIntoImage(ccdn, row, col, self.rowbuf)

    def storeBufferedDataIntoImage(self, ccd, rw, cl, data):
        """
        Move data from row buffer (of 2 or 4 rows) into final image
        :param ccdn: the CCD numbers2
        :param rw: the row in the CCD
        :param cl: the column in the CCD
        :param data: the data (already uncompressed)
        :return:
        """
        rows = (4 if not self.is2RowArea else 2)
        rowsRange = range(0, rows)

        print('Move blocks: ', end='', flush=True)
        for drow in rowsRange:
            if self.isQuadE: # Quadrant E
                self.images[ccd][rw + drow, 0:VISSize.COLS_HALF] = data[drow, :]
                print('Row {} ({}px => ({}, 0:{})  '.format(drow, VISSize.COLS_HALF, rw + drow,
                                                            VISSize.COLS_HALF), end='', flush=True)
            elif self.isQuadF:  # Quadrant F
                self.images[ccd][rw + drow, -1:-VISSize.COLS_HALF - 1:-1] = data[drow, :]
                print('Row {} ({}px => ({}, -1:{})  '.format(drow, VISSize.COLS_HALF, rw + drow,
                                                             -VISSize.COLS_HALF - 1), end='', flush=True)
            elif self.isQuadG:  # Quadrant G
                self.images[ccd][rw - drow, -1:-VISSize.COLS_HALF - 1:-1] = data[drow, :]
                print('Row {} ({}px => ({}, -1:{})  '.format(drow, VISSize.COLS_HALF, rw - drow,
                                                             -VISSize.COLS_HALF - 1), end='', flush=True)
            elif self.isQuadH:  # Quadrant H
                self.images[ccd][rw - drow, 0:VISSize.COLS_HALF] = data[drow, :]
                print('Row {} ({}px => ({}, 0:{})  '.format(drow, VISSize.COLS_HALF, rw - drow,
                                                            VISSize.COLS_HALF), end='', flush=True)
        print('', flush=True)

        self.storedBlocks = 0

    def process_input(self):
        """
        Run the processing of the input file
        :return:
        """
        n = 0
        nn = []
        self.comprType = ComprType.NO_COMPR
        self.comprPrs = 16

        # For compression with reordering
        self.rowbuf = np.zeros((4, VISSize.COLS_HALF), dtype=np.uint16)
        print('{}'.format(self.rowbuf.shape), flush=True)
        self.storedBlocks = 0

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
                        logger.info(f'Read {self.visHdr.size} bytes of main header')

                        self.comprType = 1 #self.visHdr.compressionInfo.compr_type
                        self.comprPrs = self.visHdr.compressionInfo.compr_prs
                        self.isCompressed = self.visHdr.compressionInfo.compr_type != ComprType.NO_COMPR.value
                        self.mustReorder = self.visHdr.compressionInfo.compr_type == ComprType.WITH_REORDER_121.value

                        self.npackets_hdr = self.npackets_hdr + 1
                        self.nbytes = self.nbytes + self.visHdr.size
                    else:
                        logger.error('Cannot read file header.')
                        return

                elif word == RAWVISSciDataPacket.InitialMark:
                    # Science packet
                    if not self.visSciPck.read(fh): break

                    logger.debug(self.visSciPck.info())

                    n = n + 1
                    self.npackets = self.npackets + 1
                    self.nbytes = self.nbytes + self.visSciPck.size

                    # Put data into image
                    ccdn = self.visSciPck.ccdId.ccd_id
                    if ccdn >= len(self.images):
                        logger.info(f'Reading data for CCD {ccdn}')
                        self.images.append(np.zeros((VISSize.ROWS, VISSize.COLS), dtype=np.uint16))
                        self.ccd_number.append(ccdn + 1)

                    row = self.visSciPck.ccdId.row
                    col = self.visSciPck.ccdId.col
                    bindata = self.visSciPck.binarray
                    bindataLen = self.visSciPck.dataLength.data

                    self.defineQuadrant(row, col)

                    s = '{:>06s}{:>013s}{:>013s}{:>016s}'.format(\
                        bin(self.visSciPck.ccdId.ccd_id)[2:], bin(row)[2:], bin(col)[2:], bin(bindataLen)[2:])

                    # print(('CCD {} {:4d} {:4d} , {:5d} bytes => {:>06s}|{:>013s}|{:>013s} ' +
                    #        '=> {:8s} {:8s} {:8s} {:8s} {:8s} {:8s}').format(\
                    #       self.visSciPck.ccdId.ccd_id, row, col, bindataLen,
                    #       bin(self.visSciPck.ccdId.ccd_id)[2:], bin(row)[2:], bin(col)[2:],
                    #       s[:8],s[8:16],s[16:24],s[24:32],s[32:40],s[40:]))

                    print(('CCD {} {:4d} {:4d} => ').\
                        format(self.visSciPck.ccdId.ccd_id, row, col), end='', flush=True)

                    if not self.isCompressed:

                        dataRow = np.array(self.row_unpacker.unpack(bindata), dtype=np.uint8)
                        self.storeDataAtImageDirect(ccdn, row, col, dataRow)

                    else:

                        dataRow = self.uncompressData(bindata)
                        pprint(dataRow.shape)
                        if self.mustReorder:
                            self.storeDataAtImageReordered(ccdn, row, col, dataRow)
                        else:
                            self.storeDataAtImageDirect(ccdn, row, col, dataRow)

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
            logger.warning('Full-FPA output format still not supported')

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
