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

import os
import sys

_filedir_ = os.path.dirname(__file__)
_appsdir_, _ = os.path.split(_filedir_)
_basedir_, _ = os.path.split(_appsdir_)
sys.path.insert(0, os.path.abspath(os.path.join(_filedir_, _basedir_, _appsdir_)))

PYTHON2 = False
PY_NAME = "python3"
STRING = str

#----------------------------------------------------------------------

from struct import Struct

from pprint import pprint

import logging
logger = logging.getLogger()

#----------------------------------------------------------------------

VERSION = '0.0.1'

__author__     = "J C Gonzalez"
__version__    = VERSION
__license__    = "LGPL 3.0"
__status__     = "Development"
__copyright__  = "Copyright (C) 2015-2019 by Euclid SOC Team @ ESAC / ESA"
__email__      = "jcgonzalez@sciops.esa.int"
__date__       = "June 2019"
__maintainer__ = "J C Gonzalez"
#__url__       = ""

#----------------------------------------------------------------------

SequenceIdName = ['ONLY READOUT',
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

class CompressionInfo:
    """
    Class CompressionInfo

    Contains fields with information on VIS RAW data compression
    """
    def __init__(self):
        self.data = 0 # 2-bytes
        self.mode = 0 # 2 bits
        self.comprType = 0 # 2 bits
        self.comprPrs = 0 # 12 bits
        self.pck = Struct('>H')

    def unpack(self, bindata):
        self.data = self.pck.unpack(bindata)[0]
        self.mode = (self.data >> 14) & 0x00000003
        self.comprType = (self.data >> 12) & 0x00000003
        self.comprPrs = self.data  & 0x00000fff
        return (self.mode, self.comprType, self.comprPrs)

    def pack(self, items):
        self.mode, self.comprType, self.comprPrs = items
        self.data = (((self.mode & 0x00000003) << 14) | \
                     ((self.comprType & 0x00000003) << 12) | \
                      (self.comprPrs & 0x00000fff))
        return self.pck.pack(self.data)

    def info(self, items):
        _ = self.pack(items)
        return '(Mode: {}, ComprType: {}, ComprPrs: {} px per block)'.\
            format('SCIENCE' if self.mode == 0 else 'MANUAL',
                   ['No Compr', '121 Without reordering', '121 With reordering',''][self.comprType],
                   self.comprPrs)

class ExposureDuration:
    """
    Class ExposureDuration

    Contains fields with ROE Exposure duration fields
    """
    def __init__(self):
        self.elemsize = 4
        self.numelems = 12
        self.elemsets = 2
        self.exposureDuration = [0] * self.numelems * self.elemsets
        self.pck = Struct('>{}I'.format(self.numelems * self.elemsets))

    def unpack(self, bindata):
        self.exposureDuration = self.pck.unpack(bindata)
        return [self.exposureDuration[::2],
                self.exposureDuration[1::2]]

    def pack(self, item):
        x = [0] * self.numelems * self.elemsets
        for i in range(0,12):
            x[2 * i] = item[0][i]
            x[2 * i + 1] = item[1][i]
        self.exposureDuration = x[:]
        return self.pck.pack(*self.exposureDuration)

    def info(self, item):
        _ = self.pack(item)
        x = self.exposureDuration
        dur = [x[i] << 32 + x[i + 1] for i in range(0,24,2)]
        return ["{} ms".format(x) for x in dur]

class VersionSeqConf:
    """
    Class VersionSeqConf

    Contains fields with Version Seq. Configs.
    """
    def __init__(self):
        self.elemsize = 2
        self.numelems = 12
        self.verseqconf = [0] * self.numelems
        self.pck = Struct('>{}H'.format(self.numelems))

    def unpack(self, bindata):
        self.verseqconf = self.pck.unpack(bindata)
        return self.verseqconf

    def pack(self, item):
        return self.pck.pack(*item)

class ConfigTables:
    """
    Class ConfigTables

    Contains the Header Config. Tables data
    """
    def __init__(self):
        self.elemsize = 2
        self.numelems = 3
        self.cfgSineTableId = 0
        self.cfgFreqTableId = 0
        self.cfgShortFreqTableId = 0
        self.pck = Struct('>{}H'.format(self.numelems))

    def unpack(self, bindata):
        self.cfgSineTableId, \
        self.cfgFreqTableId, \
        self.cfgShortFreqTableId = self.pck.unpack(bindata)
        return (self.cfgSineTableId,
                self.cfgFreqTableId,
                self.cfgShortFreqTableId)

    def pack(self, items):
        self.cfgSineTableId, \
        self.cfgFreqTableId, \
        self.cfgShortFreqTableId = items
        return self.pck.pack(self.cfgSineTableId,
                             self.cfgFreqTableId,
                             self.cfgShortFreqTableId)

class TCParameters:
    """
    Class TCParameters

    Contains the TC Parameters information
    """
    def __init__(self):
        self.size = 74
        self.tcparams = [0] * self.size
        self.pck = Struct('>{}B'.format(self.size))

    def unpack(self, bindata):
        self.tcparams = self.pck.unpack(bindata)
        return self.tcparams

    def pack(self, item):
        return self.pck.pack(*item)

class LE1VISHeader:
    """
    Class LE1VISHeader

    LE1 VIS RAW Data File Header
    """
    def __init__(self):
        """
        Initialization method
        """
        self.rawdata = b''
        self.pck = {
            "Space_Wire_Packet_Header":  (Struct('>I'), 4),
            "Operation_Id":              (Struct('>I'), 4),
            "Compression_Info":          (CompressionInfo(), 2),
            "Start_Time":                (Struct('>6B'), 6),
            "Exposure_Duration":         (ExposureDuration(), 4 * 2 * 12),
            "Image_Size":                (Struct('>I'), 4),
            "Vertical_Start":            (Struct('>H'), 2),
            "Vertical_End":              (Struct('>H'), 2),
            "Mdu_Size":                  (Struct('>H'), 2),
            "End_Time":                  (Struct('>6B'), 6),
            "Sequence_Id":               (Struct('>H'), 2),
            "Config3D_Id":               (Struct('>H'), 2),
            "Version_SeqConf":           (VersionSeqConf(), 2 * 12),
            "Readout_Count":             (Struct('>H'), 2),
            "Config_Tables":             (ConfigTables(), 2 * 3),
            "TC_Parameters":             (TCParameters(), 74),
            "ASW_Version":               (Struct('>H'), 2),  # TODO: This is in fact I (4 bytes) in ICD 4.0d9
         #   "RSU_Cfg_Status":            (Struct('>H'), 2), # TODO: This appears in ICD 4.0d9
            "CRC_16":                    (Struct('>H'), 2),
            "Space_Wire_Packet_Footer":  (Struct('>I'), 4)
        }
        self.data = {}
        self.size = sum([v[1] for k,v in self.pck.items()])

    def unpack(self, bindata):
        """
        Unpack bindata into data fields
        :param bindata: Binary data stream
        :return: True if unpacking is OK, False otherwise
        """
        try:
            i = 0
            for k,v in self.pck.items():
                pck, size = v
                x = pck.unpack(bindata[i:i+size])
                if isinstance(x, int):
                    self.data[k] = x
                elif len(x) > 1:
                    self.data[k] = list(x)
                else:
                    self.data[k] = x[0]
                print('Unpacking {} with {} (size={} => {})'.format(k, pck, size, len(x)))
                i = i + size
        except Exception as excpt:
            raise
            return False
        return True

    def pack(self):
        """
        Packs data into a binary stream
        :return: The binary stream
        """
        try:
            bindata = b''
            for k,v in self.pck.items():
                pck, size = v
                #if isinstance(pck, Struct):
                x = self.data[k]
                if isinstance(x, int):
                    bindata = bindata + pck.pack(x)
                elif isinstance(pck, Struct):
                    bindata = bindata + pck.pack(*x)
                else:
                    bindata = bindata + pck.pack(x)
            return bindata
        except Exception as excpt:
            raise
            return None

    def read(self, fh):
        """
        Read the packed data header from the file handler
        :param fhdl: The file handler
        :return: True if unpacking is OK, False otherwise
        """
        bindata = fh.read(self.size)
        pprint(bindata)
        return self.unpack(bindata)

    def write(self, fh):
        """
        Read the packed data header from the file handler
        :param fhdl: The file handler
        :return: True if unpacking is OK, False otherwise
        """
        try:
            bindata = self.pack()
            fh.write(bindata)
        except Exception as excpt:
            raise
            return False
        return True
    
    def info(self):
        """
        Show the header information in a nice way
        :return: -
        """
        x = self.data
        p = self.pck
        print(("{}\n" +
               "Space_Wire_Packet_Header: 0x{:08X}\n" +
               "Operation_Id (SOC Id)     {:010d}\n" +
               "Compression_Info:         {}\n" +
               "Start_Time (MJD):         {}\n" +
               "Exposure_Duration:        {}\n" +
               "Image_Size:               {}\n" +
               "Vertical_Start:           0x{:04X}\n" +
               "Vertical_End:             0x{:04X}\n" +
               "Mdu_Size:                 {}\n" +
               "End_Time (MJD)            {}\n" +
               "Sequence_Id:              {} - {}\n" +
               "Config3D_Id:              {}\n" +
               "Version_SeqConf:          {}\n" +
               "Readout_Count:            {}\n" +
               "Config_Tables:            {}\n" +
               "TC_Parameters:            {}\n" +
               "ASW_Version:              {}\n" +
               # "RSU_Cfg_Status:           {}\n" +
               "CRC_16:                   0x{:04X}\n" +
               "Space_Wire_Packet_Footer: 0x{:08X}\n" +
               "{}\n" +
               "{} bytes").\
              format('-' * 60,
                     x["Space_Wire_Packet_Header"],
                     x["Operation_Id"],
                     p["Compression_Info"][0].info(x["Compression_Info"]),
                     sum([x["Start_Time"][i] << (8 * (5 - i)) for i in range(0,6)]),
                     p["Exposure_Duration"][0].info(x["Exposure_Duration"]),
                     x["Image_Size"],
                     x["Vertical_Start"],
                     x["Vertical_End"],
                     x["Mdu_Size"],
                     sum([x["End_Time"][i] << (8 * (5 - i)) for i in range(0, 6)]),
                     x["Sequence_Id"], SequenceIdName[x["Sequence_Id"]],
                     x["Config3D_Id"],
                     x["Version_SeqConf"],
                     x["Readout_Count"],
                     x["Config_Tables"],
                     '<none>', # x["TC_Parameters"],
                     x["ASW_Version"],
                     # x["RSU_Cfg_Status"],
                     x["CRC_16"],
                     x["Space_Wire_Packet_Footer"],
                     '-' * 60,
                     self.size))
        


def main():

    rawFile = "/Users/jcgonzalez/ws/LE1/LE1-VIS-Dockeen-Generation/data/" + \
              "VIS_SPW1N_20190910_090045_00001.bin"

    le1visHdr = LE1VISHeader()
    with open(rawFile, 'rb') as fh:
        isRead = le1visHdr.read(fh)
        if isRead:
            le1visHdr.info()
            with open(rawFile + '.dup', 'wb') as fw:
                le1visHdr.write(fw)
        else:
            print('Cannot read file header.')


if __name__ == '__main__':
    main()
