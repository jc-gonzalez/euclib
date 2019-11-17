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

from pprint import pprint
from enum import Enum

# Project
from basic import Encoded

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

SEQUENCE_ID_NAME = ['ONLY READOUT',
                    'SIMULATED SIENCE',
                    'BIAS',
                    'BIAS With LIMITED SCAN',
                    'CHARGE INJECTION',
                    'DARK',
                    'DARK With LIMITED SCAN',
                    'FLATFIELD',
                    'LINEARITY`',
                    'NOMINAL/SHORT',
                    'NOMINAL/SHORT with LIMITED SCAN',
                    'NOMINAL with CHARGE INJECTION',
                    'SERIAL TRAP PUMPING',
                    'SERIAL TRAP PUMPING with MULTIPLE READING',
                    'VERTICAL TRAP PUMPING']

MSK32 = 0xffffffff
MSK16 = 0xffff
MSK8 = 0xff

class ComprMode(Enum):
    """
    Compression Mode: 0: Science, 1: Manual
    """
    SCIENCE = 0
    MANUAL = 1


class ComprType(Enum):
    """
    Compression Type:
    0: No Compr
    1: 121 Without reordering
    2: 121 With reordering
    """
    NO_COMPR = 0
    WITHOUT_REORDER_121 = 1
    WITH_REORDER_121 = 2


class HexInt(Encoded):
    """
    Integer encoded field, to be shown as hex. value
    """
    def __str__(self):
        """
        String representation of the hex. integer
        """
        return '0x{:0{hwd}X}'.format(self.data, hwd=self.nbytes*2)


class MultyByteIntMsLs(Encoded):
    """
    Integer encoded field, with a custom number of bytes (MS to LS)
    """
    def unpack(self, binstr):
        """
        Unpack from the provided binary string the required data
        :return: The unpacked value
        """
        x = super().unpack(binstr)
        self.data = sum([self.bindata[i] << (8 * (self.nbytes - i -1 ))
                         for i in range(0, self.nbytes)])


class CompressionInfo(Encoded):
    """
    Class CompressionInfo

    Contains fields with information on VIS RAW data compression
    """
    def __init__(self, name, fmt, nbytes):
        """
        Initialize class instance
        """
        super().__init__(name, fmt, nbytes)
        self.mode = 0 # 2 bits
        self.compr_type = 0 # 2 bits
        self.compr_prs = 0 # 12 bits

    def set(self, mode, compr_type, compr_prs, compr_info=None):
        """
        Set the different components of the Compression Info object,
        or the entire set of bytes at once
        """
        if compr_info is None:
            self.mode = mode
            self.compr_type = compr_type
            self.compr_prs = compr_prs
            super().set(((self.mode & 0x00000003) << 14) | \
                        ((self.compr_type & 0x00000003) << 12) | \
                        (self.compr_prs & 0x00000fff))
        else:
            super().set(compr_info)
            self.mode = (self.data >> 14) & 0x00000003
            self.compr_type = (self.data >> 12) & 0x00000003
            self.compr_prs = self.data  & 0x00000fff

    def pack(self, mode=None, compr_type=None, compr_prs=None, compr_info=None):
        """
        Pack object into binary string
        :return: The resulting packed bin. string
        """
        if (mode is not None) or (compr_info is not None):
            self.set(mode, compr_type, compr_prs, compr_info)
        return super().pack()

    def unpack(self, binstr):
        """
        Unpack the object components from the binary string provided
        """
        _ = super().unpack(binstr)
        self.mode = (self.data >> 14) & 0x00000003
        self.compr_type = (self.data >> 12) & 0x00000003
        self.compr_prs = self.data  & 0x00000fff
        return (self.mode, self.compr_type, self.compr_prs)

    def __str__(self):
        """
        Provides a info string for the underlying variable
        :return: The info string in the form 'name: value'
        """
        return '(Mode: {}, ComprType: {}, ComprPrs: {} px per block)'.\
            format('SCIENCE' if self.mode == ComprMode.SCIENCE else 'MANUAL',
                   ['No Compr',
                    '121 Without reordering',
                    '121 With reordering', ''][self.compr_type],
                   self.compr_prs)


class ExposureDuration(Encoded):
    """
    Class ExposureDuration

    Contains fields with ROE Exposure duration fields
    """
    def __init__(self, name, fmt, nbytes):
        """
        Initialize class instance
        """
        super().__init__(name, fmt, nbytes)
        self.numelems = 12
        self.elemsets = 2
        self.n = self.numelems * self.elemsets
        self.exposure_duration = [0] * self.numelems

    def set(self, durations):
        """
        Set the different values of the durations, as well as the
        different MS and LS values
        """
        self.exposure_duration = durations
        self.data = [[(d >> 32) & MSK32, d & MSK32] for d in durations]
        self.bindata = [x for pair in self.data for x in pair]

    def pack(self, durations=None):
        """
        Pack the internal data value
        :return: The packed binary string
        """
        if durations is not None:
            self.set(durations)
        return super().pack()

    def unpack(self, binstr):
        """
        Unpack from the provided binary string the required data
        :return: The unpacked value
        """
        self.bindata = self.pck.unpack(binstr)
        x = self.bindata
        self.data = [[x[i] << 32, x[i + 1]] for i in range(0, self.n, 2)]
        self.exposure_duration = [x[0] << 32 + x[1] for x in self.data]
        return self.exposure_duration

    def __str__(self):
        """
        Provides a info string for the underlying variable
        :return: The info string in the form 'name: value'
        """
        x = self.exposure_duration
        return ', '.join(["{}:{} ms".format(i+1, x[i]) for i in range(0, len(x))])


class VersionSeqConf(Encoded):
    """
    Class VersionSeqConf

    Contains fields with Version Seq. Configs.
    """
    def __init__(self, name, fmt, nbytes):
        """
        Initialize class instance
        """
        super().__init__(name, fmt, nbytes)
        self.numelems = 12
        self.verseqconf = [0] * self.numelems

    def unpack(self, binstr):
        """
        Unpack from the provided binary string the required data
        :return: The unpacked value
        """
        _ = super().unpack(binstr)
        self.data = list(self.bindata)
        self.verseqconf = self.data
        return self.data


class ConfigTables(Encoded):
    """
    Class ConfigTables

    Contains the Header Config. Tables data
    """
    def __init__(self, name, fmt, nbytes):
        """
        Initialize class instance
        """
        super().__init__(name, fmt, nbytes)
        self.elemsize = 2
        self.numelems = 3
        self.cfg_sine_table_id = 0
        self.cfg_freq_table_id = 0
        self.cfg_short_freq_table_id = 0

    def pack(self, st=None, ft=None, sft=None):
        """
        Pack the internal data value
        :return: The packed binary string
        """
        if (st is not None) and (ft is not None) and (sft is not None):
            self.cfg_sine_table_id, \
            self.cfg_freq_table_id, \
            self.cfg_short_freq_table_id = (st, ft, sft)
            self.data = (st, ft, sft)
        return super().pack()

    def unpack(self, binstr):
        """
        Unpack from the provided binary string the required data
        :return: The unpacked value
        """
        _ = super().unpack(binstr)
        self.data = list(self.bindata)
        self.cfg_sine_table_id, \
        self.cfg_freq_table_id, \
        self.cfg_short_freq_table_id = self.data
        return (self.cfg_sine_table_id,
                self.cfg_freq_table_id,
                self.cfg_short_freq_table_id)


class TCParameters(Encoded):
    """
    Class TCParameters

    Contains the TC Parameters information
    """
    def __init__(self, name, fmt, nbytes):
        """
        Initialize class instance
        """
        super().__init__(name, fmt, nbytes)
        self.tcparams = [0] * self.size


class CcdId(Encoded):
    """
    Class CcdID

    Contains fields with information on CCD-ID, column and row for the science
    data packet
    """
    def __init__(self, name, fmt, nbytes):
        """
        Initialize class instance
        """
        super().__init__(name, fmt, nbytes)
        self.ccd_id = 0 # 6 bits
        self.col = 0 # 13 bits
        self.row = 0 # 13 bits

    def set(self, ccd_id, col, row, ccdid_info=None):
        """
        Set the different components of the CCD ID object
        or the entire set of bytes at once
        """
        if ccdid_info is None:
            self.ccd_id = ccd_id
            self.col = col
            self.row = row
            super().set(((self.ccd_id & 0x00000007f) << 26) | \
                        ((self.col & 0x00001fff) << 13) | \
                        (self.row & 0x00001fff))
        else:
            super().set(ccdid_info)
            self.ccd_id = (self.data >> 26) & 0x0000007f
            self.col = (self.data >> 13) & 0x00001fff
            self.row = self.data  & 0x00001fff

    def pack(self, ccd_id=None, col=None, row=None, ccdid_info=None):
        """
        Pack object into binary string
        :return: The resulting packed bin. string
        """
        if (ccd_id is not None) or (ccdid_info is not None):
            self.set(ccd_id, col, row, ccdid_info)
        return super().pack()

    def unpack(self, binstr):
        """
        Unpack the object components from the binary string provided
        """
        _ = super().unpack(binstr)
        self.ccd_id = (self.data >> 26) & 0x0000007f
        self.col = (self.data >> 13) & 0x00001fff
        self.row = self.data & 0x00001fff
        return (self.ccd_id, self.col, self.row)

    def __str__(self):
        """
        Provides a info string for the underlying variable
        :return: The info string in the form 'name: value'
        """
        return 'CCD# {}, Pos: ({}, {})'.\
            format(self.ccd_id, self.row, self.col)


def main():
    pass


if __name__ == '__main__':
    main()
