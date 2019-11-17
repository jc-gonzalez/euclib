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

import numpy as np

from astropy.io import fits
from pprint import pprint
from struct import Struct

from le1_vis import InputType, OutputType, \
                    RAWVISHeader, RAWVISHeader_prev, RAWVISHeader_old, \
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
LOGGER = logging.getLogger()

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

        self.input_type = None
        self.output_type = None

        self.input_file = None
        self.output_dir = None

        pprint(args)

    def run(self):
        pass


def main():
    pass

    # #rawFile = "/Users/jcgonzalez/ws/LE1/LE1-VIS-Dockeen-Generation/data/" + \
    # #          "VIS_SPW1N_20190910_090045_00001.bin"
    #
    # rawFile = "/Users/jcgonzalez/ws/LE1/LE1-VIS-Dockeen-Generation/data/" + \
    #           "QH_CCD2_ZOD_721_321_MIXED__NO_COMPRESSED.bin"
    #
    #
    # self.visHdr = RAWVISHeader()
    # self.visSciPck = RAWVISSciDataPacket()
    #
    # npackets_roe = []
    # nbytes = 0
    # npackets = 0
    # npackets_hdr = 0
    # n = 0
    # nn = []
    #
    # images = []
    # ccd_number = []
    #
    # row_unpacker_fmt = '{}H'.format(VISSize.COLS_HALF)
    # row_unpacker = Struct(row_unpacker_fmt)
    #
    # with open(rawFile, 'rb') as fh:
    #     while True:
    #         word = read_4_byte_word(fh)
    #         if word == 0xFFFFFFFF:
    #             npackets_roe.append(npackets)
    #             nn.append(n)
    #             n = 0
    #             # Header packet
    #             isRead = self.visHdr.read(fh)
    #             if isRead:
    #                 self.visHdr.info()
    #                 npackets_hdr = npackets_hdr + 1
    #                 nbytes = nbytes + self.visHdr.size
    #             else:
    #                 print('Cannot read file header.')
    #                 return
    #         elif word == 0xEEEEEEEE:
    #             # Science packet
    #             isRead = self.visSciPck.read(fh)
    #             if isRead:
    #                 n = n + 1
    #                 #print('{:5d} CCD-ID: {} - {} ({}) bytes'.\
    #                 #      format(n,
    #                 #             self.visSciPck.ccdId,
    #                 #             self.visSciPck.dataLength,
    #                 #             self.visSciPck.size))
    #                 npackets = npackets + 1
    #                 nbytes = nbytes + self.visSciPck.size
    #
    #                 # Put data into image
    #                 ccdn = self.visSciPck.ccdId.ccd_id
    #                 if ccdn >= len(images):
    #                     print(ccdn)
    #                     images.append(np.zeros((VISSize.ROWS, VISSize.COLS), dtype=int))
    #                     ccd_number.append(ccdn + 1)
    #
    #                 row = self.visSciPck.ccdId.row
    #                 col = self.visSciPck.ccdId.col
    #                 dataRow = np.array(row_unpacker.unpack(visPck.data.binstr))
    #
    #                 if col == 0:
    #                     if row < VISSize.ROWS_HALF:
    #                         # Q1: E
    #                         images[ccdn][row,0:VISSize.COLS_HALF] = dataRow
    #                     else:
    #                         # Q4: H
    #                         images[ccdn][row,0:VISSize.COLS_HALF] = dataRow
    #                 else:
    #                     if row < VISSize.ROWS_HALF:
    #                         # Q2: F
    #                         images[ccdn][row,-1:-VISSize.COLS_HALF-1:-1] = dataRow
    #                     else:
    #                         images[ccdn][row,-1:-VISSize.COLS_HALF-1:-1] = dataRow
    #                         # Q3: G
    #
    #             else:
    #                 break
    #         else:
    #             if word != -1:
    #                 print(f'Read from file: 0x{word:08X}')
    #             break
    #
    # nn.append(n)
    # npackets_roe.append(npackets)
    # npackets_per_roe = [x-y for x,y in zip(npackets_roe[1:], npackets_roe[:-1])]
    #
    # print(f'{nbytes} bytes')
    # print(f'{npackets_hdr} header packets')
    # print(f'{npackets} science packets')
    # print('Sci.Packets per ROE: {}'.\
    #       format(', '.\
    #              join(['{}:{}'.format(i+1, npackets_per_roe[i]) \
    #                    for i in range(0, len(npackets_per_roe))])))
    #
    # # Primary HDU with general info
    # ## hdu0 = fits.PrimaryHDU()
    # ## hdul = fits.HDUList([hdu0])
    # ##
    # ## # Then, an extension with each image, without any actual order
    # ## for ccdn,img in zip(ccd_number, images):
    # ##     hdu = fits.ImageHDU(img)
    # ##     hdu.header['CCD_NUM'] = ccdn
    # ##     hdul.append(hdu)
    # ##
    # ## hdul.writeto('test.fits', overwrite=True)
    #
    #
    # # Then, an extension with each image, without any actual order
    # for ccdn,img in zip(ccd_number, images):
    #     hdu = fits.PrimaryHDU(img)
    #     hdu.header['CCD_NUM'] = ccdn
    #     hdul = fits.HDUList([hdu])
    #     hdul.writeto('test_{:02d}.fits'.format(ccdn), overwrite=True)


if __name__ == '__main__':
    main()
