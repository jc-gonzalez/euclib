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
from struct import unpack
from enum import IntEnum

from basic import Encoded
from le1_base import SEQUENCE_ID_NAME, \
                     ComprMode, ComprType, \
                     HexInt, MultyByteIntMsLs, \
                     CompressionInfo, ExposureDuration, VersionSeqConf, \
                     ConfigTables, TCParameters, \
                     CcdId

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

class VISSize:
    ROWS = 4172
    COLS = 4256
    ROWS_HALF = ROWS // 2
    COLS_HALF = COLS // 2

    ROWS_FPA = ROWS
    COLS_FPA = COLS
    ROWS_QUAD = ROWS_HALF
    COLS_QUAD = COLS_HALF


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

Str2InputType = [(['raw', 'icd-4.0d9', '4.0d9'], InputType.RAW),
                 (['raw-prev', 'raw_prev', 'prev', 'icd-4.0d8', '4.0d8'], InputType.RAW_PREV),
                 (['raw-old', 'raw_old', 'old', 'icd-3.4'], InputType.RAW_OLD),
                 (['le1'], InputType.LE1)]
InputTypeStrChoices = [x for sl,t in Str2InputType for x in sl]

class OutputType(IntEnum):
    LE1 = 0,
    FULL_FPA = 1,
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
                  (['fullfpa', 'full-fpa', 'fpa'], OutputType.FULL_FPA)]
OutputTypeStrChoices = [x for sl,t in Str2OutputType for x in sl]


class RAWVISHeader:
    """
    Class RAWVISHeader

    LE1 VIS RAW Data File Header (compliant with ICD 4.0 draft 9)
    """
    def __init__(self):
        """
        Initialization method
        """
        # Fields
        self.spaceWirePcktHdr = HexInt('Space_Wire_Packet_Header', '>I', 4)
        self.operationId = Encoded('Operation_Id', '>I', 4)
        self.compressionInfo = CompressionInfo('Compression_Info', '>H', 2)
        self.startTime = MultyByteIntMsLs('Start_Time', '>6B', 6)
        self.exposureDuration = ExposureDuration('Exposure_Duration', '>24I', 4 * 2 * 12)
        self.imageSize = Encoded('Image_Size', '>I', 4)
        self.verticalStart = HexInt('Vertical_Start', '>H', 2)
        self.verticalEnd = HexInt('Vertical_End', '>H', 2)
        self.mduSize = Encoded('Mdu_Size', '>H', 2)
        self.spare4 = Encoded('Spare4', '>I', 4)
        self.endTime = MultyByteIntMsLs('End_Time', '>6B', 6)
        self.sequenceId = Encoded('Sequence_Id', '>H', 2)
        self.config3DId = Encoded('Config3D_Id', '>H', 2)
        self.versionSeqConf = VersionSeqConf('Version_SeqConf', '>12H', 2 * 12)
        self.readoutCount = Encoded('Readout_Count', '>H', 2)
        self.configTables = ConfigTables('Config_Tables', '>3H', 2 * 3)
        self.tcParameters = TCParameters('TC_Parameters', '>74B', 74)
        self.aswVersion = Encoded('ASW_Version', '>I', 4)
        self.rsuCfgStatus = Encoded('RSU_Cfg_Status', '>H', 2)
        self.crc16 = HexInt('CRC_16', '>H', 2)
        self.spaceWirePcktFtr = HexInt('Space_Wire_Packet_Footer', '>I', 4)

        self.fields = [
            self.spaceWirePcktHdr,
            self.operationId,
            self.compressionInfo,
            self.startTime,
            self.exposureDuration,
            self.imageSize,
            self.verticalStart,
            self.verticalEnd,
            self.mduSize,
            self.spare4,
            self.endTime,
            self.sequenceId,
            self.config3DId,
            self.versionSeqConf,
            self.readoutCount,
            self.configTables,
            self.tcParameters,
            self.aswVersion,
            self.rsuCfgStatus,
            self.crc16,
            self.spaceWirePcktFtr
        ]
        self.rawdata = b''
        self.size = sum([x.nbytes for x in self.fields])

    def pack(self):
        """
        Packs data into a binary stream
        :return: The binary stream
        """
        try:
            bindata = b''
            for f in self.fields:
                bindata = bindata + f.pack()
            self.rawdata = bindata
            return bindata
        except Exception as excpt:
            raise
            return None

    def unpack(self, bindata):
        """
        Unpack bindata into data fields
        :param bindata: Binary data stream
        :return: True if unpacking is OK, False otherwise
        """
        try:
            i = 0
            self.rawdata = bindata[:self.size]
            for f in self.fields:
                x = f.unpack(bindata[i:i+f.nbytes])
                i = i + f.nbytes
        except Exception as excpt:
            raise
            return False
        return True

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
            self.rawdata = self.pack()
            fh.write(self.rawdata)
        except Exception as excpt:
            raise
            return False
        return True

    def info(self):
        """
        Show the header information in a nice way
        :return: -
        """
        print(('-' * 60) + '\n' +
              ('Space_Wire_Packet_Header: {}\n' +
               'Operation_Id (SOC Id)     {:010d}\n' +
               'Compression_Info:         {}\n' +
               'Start_Time (MJD):         {}\n' +
               'Exposure_Duration:        {}\n' +
               'Image_Size:               {}\n' +
               'Vertical_Start:           {}\n' +
               'Vertical_End:             {}\n' +
               'Mdu_Size:                 {}\n' +
               'End_Time (MJD)            {}\n' +
               'Sequence_Id:              {} - {}\n' +
               'Config3D_Id:              {}\n' +
               'Version_SeqConf:          {}\n' +
               'Readout_Count:            {}\n' +
               'Config_Tables:            {}\n' +
               'TC_Parameters:            {}\n' +
               'ASW_Version:              {}\n' +
               'RSU_Cfg_Status:           {}\n' +
               'CRC_16:                   {}\n' +
               'Space_Wire_Packet_Footer: {}\n' +
               '{} bytes\n').\
              format(self.spaceWirePcktHdr,
                     self.operationId.data,
                     self.compressionInfo,
                     self.startTime,
                     self.exposureDuration,
                     self.imageSize,
                     self.verticalStart.data,
                     self.verticalEnd.data,
                     self.mduSize,
                     self.endTime,
                     self.sequenceId.data, SEQUENCE_ID_NAME[self.sequenceId.data],
                     self.config3DId,
                     self.versionSeqConf,
                     self.readoutCount,
                     self.configTables,
                     '<none>', # self.tcParameters,
                     self.aswVersion,
                     self.rsuCfgStatus,
                     self.crc16,
                     self.spaceWirePcktFtr,
                     self.size) +
              ('-' * 60) + '\n')


class RAWVISHeader_prev(RAWVISHeader):
    """
    Class RAWVISHeader_old

    LE1 VIS RAW Data File Header, based on ICD 4.0 draft ?
    """
    def __init__(self):
        """
        Initialization method
        """
        super().__init__()

        self.fields = [
            self.spaceWirePcktHdr,
            self.operationId,
            self.compressionInfo,
            self.startTime,
            self.exposureDuration,
            self.imageSize,
            self.verticalStart,
            self.verticalEnd,
            self.mduSize,
            self.endTime,
            self.sequenceId,
            self.config3DId,
            self.versionSeqConf,
            self.readoutCount,
            self.configTables,
            self.tcParameters,
            self.aswVersion,
            # self.rsuCfgStatus,  # TODO: Include to comply with ICD 4.0d9
            self.crc16,
            self.spaceWirePcktFtr
        ]
        self.size = sum([x.nbytes for x in self.fields])

    def info(self):
        """
        Show the header information in a nice way
        :return: -
        """
        print(('-' * 60) + '\n' +
              ('Space_Wire_Packet_Header: {}\n' +
               'Operation_Id (SOC Id)     {:010d}\n' +
               'Compression_Info:         {}\n' +
               'Start_Time (MJD):         {}\n' +
               'Exposure_Duration:        {}\n' +
               'Image_Size:               {}\n' +
               'Vertical_Start:           {}\n' +
               'Vertical_End:             {}\n' +
               'Mdu_Size:                 {}\n' +
               'End_Time (MJD)            {}\n' +
               'Sequence_Id:              {} - {}\n' +
               'Config3D_Id:              {}\n' +
               'Version_SeqConf:          {}\n' +
               'Readout_Count:            {}\n' +
               'Config_Tables:            {}\n' +
               'TC_Parameters:            {}\n' +
               'ASW_Version:              {}\n' +
               # 'RSU_Cfg_Status:           {}\n' +
               'CRC_16:                   {}\n' +
               'Space_Wire_Packet_Footer: {}\n' +
               '{} bytes\n').\
              format(self.spaceWirePcktHdr,
                     self.operationId.data,
                     self.compressionInfo,
                     self.startTime,
                     self.exposureDuration,
                     self.imageSize,
                     self.verticalStart.data,
                     self.verticalEnd.data,
                     self.mduSize,
                     self.endTime,
                     self.sequenceId.data, SEQUENCE_ID_NAME[self.sequenceId.data],
                     self.config3DId,
                     self.versionSeqConf,
                     self.readoutCount,
                     self.configTables,
                     '<none>', # self.tcParameters,
                     self.aswVersion,
                     # self.rsuCfgStatus,
                     self.crc16,
                     self.spaceWirePcktFtr,
                     self.size) +
              ('-' * 60) + '\n')


class RAWVISHeader_old(RAWVISHeader):
    """
    Class RAWVISHeader_old

    LE1 VIS RAW Data File Header, based on ICD 3.4
    """
    def __init__(self):
        """
        Initialization method
        """
        super().__init__()

        self.fields = [
            self.spaceWirePcktHdr,
            self.operationId,
            self.compressionInfo,
            self.startTime,
            self.exposureDuration,
            self.imageSize,
            self.verticalStart,
            self.verticalEnd,
            self.mduSize,
            self.spare4,
#            self.endTime,
#            self.sequenceId,
#            self.config3DId,
#            self.versionSeqConf,
#            self.readoutCount,
#            self.configTables,
#            self.tcParameters,
#            self.aswVersion,
#            # self.rsuCfgStatus,  # TODO: Include to comply with ICD 4.0d9
            self.crc16,
            self.spaceWirePcktFtr
        ]
        self.size = sum([x.nbytes for x in self.fields])

    def info(self):
        """
        Show the header information in a nice way
        :return: -
        """
        print(('-' * 60) + '\n' +
              ('Space_Wire_Packet_Header: {}\n' +
               'Operation_Id (SOC Id)     {:010d}\n' +
               'Compression_Info:         {}\n' +
               'Start_Time (MJD):         {}\n' +
               'Exposure_Duration:        {}\n' +
               'Image_Size:               {}\n' +
               'Vertical_Start:           {}\n' +
               'Vertical_End:             {}\n' +
               'Mdu_Size:                 {}\n' +
#               'End_Time (MJD)            {}\n' +
#               'Sequence_Id:              {} - {}\n' +
#               'Config3D_Id:              {}\n' +
#               'Version_SeqConf:          {}\n' +
#               'Readout_Count:            {}\n' +
#               'Config_Tables:            {}\n' +
#               'TC_Parameters:            {}\n' +
#               'ASW_Version:              {}\n' +
#               # 'RSU_Cfg_Status:           {}\n' +
               'CRC_16:                   {}\n' +
               'Space_Wire_Packet_Footer: {}\n' +
               '{} bytes\n').\
              format(self.spaceWirePcktHdr,
                     self.operationId.data,
                     self.compressionInfo,
                     self.startTime,
                     self.exposureDuration,
                     self.imageSize,
                     self.verticalStart.data,
                     self.verticalEnd.data,
                     self.mduSize,
#                     self.endTime,
#                     self.sequenceId.data, SEQUENCE_ID_NAME[self.sequenceId.data],
#                     self.config3DId,
#                     self.versionSeqConf,
#                     self.readoutCount,
#                     self.configTables,
#                     '<none>', # self.tcParameters,
#                     self.aswVersion,
#                     # self.rsuCfgStatus,
                     self.crc16,
                     self.spaceWirePcktFtr,
                     self.size) +
              ('-' * 60) + '\n')


class RAWVISSciDataPacket:
    """
    Class RAWVISSciDataPacket

    LE1 VIS RAW Data File Science Data Packet
    """
    def __init__(self):
        """
        Initialization method
        """
        # Fields
        self.spaceWirePcktHdr = HexInt('Space_Wire_Packet_Header', '>I', 4)
        self.operationId = Encoded('Operation_Id', '>I', 4)
        self.ccdId = CcdId('CCD-ID Col/Row', '>I', 4)
        self.dataLength = Encoded('Data_Length', '>H', 2)
        self.crc16Hdr = HexInt('CRC_16_Header', '>H', 2)
        self.data = None
        self.crc16Data = HexInt('CRC_16_Data', '>H', 2)
        self.spaceWirePcktFtr = HexInt('Space_Wire_Packet_Footer', '>I', 4)

        self.fields = [
            self.spaceWirePcktHdr,
            self.operationId,
            self.ccdId,
            self.dataLength,
            self.crc16Hdr,
            self.data,
            self.crc16Data,
            self.spaceWirePcktFtr
        ]
        self.rawdata = b''
        self.size = 0
        self.sizeHdr = sum([x.nbytes for x in [self.spaceWirePcktHdr,
                                               self.operationId,
                                               self.ccdId,
                                               self.dataLength,
                                               self.crc16Hdr]])
        self.sizeFtr = sum([x.nbytes for x in [self.crc16Data,
                                               self.spaceWirePcktFtr]])

    def pack(self):
        """
        Packs data into a binary stream
        :return: The binary stream
        """
        try:
            bindata = b''
            for f in self.fields:
                bindata = bindata + f.pack()
                #if isinstance(pck, Struct):
                # x = self.data[k]
                # if isinstance(x, int):
                #     bindata = bindata + pck.pack(x)
                # elif isinstance(pck, Struct):
                #     bindata = bindata + pck.pack(*x)
                # else:
                #     bindata = bindata + pck.pack(x)
            self.rawdata = bindata
            return bindata
        except Exception as excpt:
            raise
            return None

    def unpackHdr(self, bindata):
        """
        Unpack bindata from header section into data fields
        :param bindata: Binary data stream
        :return: True if unpacking is OK, False otherwise
        """
        try:
            nbytes = 0
            for fld in [self.spaceWirePcktHdr,
                        self.operationId,
                        self.ccdId,
                        self.dataLength,
                        self.crc16Hdr]:
                _ = fld.unpack(bindata[nbytes:nbytes+fld.nbytes])
                #pprint(fld.info())
                nbytes = nbytes + fld.nbytes
        except Exception as excpt:
            raise
            return False
        return True

    def unpackData(self, bindata):
        """
        Unpack bindata into data fields
        :param bindata: Binary data stream
        :return: True if unpacking is OK, False otherwise
        """
        sizeOfData = self.dataLength.data
        self.data = Encoded('Data', '>{}B'.format(sizeOfData), sizeOfData)
        try:
            nbytes = 0
            for fld in [self.data,
                        self.crc16Data,
                        self.spaceWirePcktFtr]:
                if fld is not None:
                    _ = fld.unpack(bindata[nbytes:nbytes+fld.nbytes])
                    nbytes = nbytes + fld.nbytes
        except Exception as excpt:
            return False
        return True

    def read(self, fh):
        """
        Read the packed data header from the file handler
        :param fhdl: The file handler
        :return: True if unpacking is OK, False otherwise
        """

        bindata = fh.read(self.sizeHdr)
        self.rawdata = bindata
        if not self.unpackHdr(bindata):
            pprint(bindata)
            return False
        if self.dataLength.data < 1:
            fh.seek(-self.sizeHdr, 1)
            self.size = 0
            return False
        self.size = self.sizeHdr + self.sizeFtr + self.dataLength.data
        bindata = fh.read(self.sizeFtr + self.dataLength.data)
        self.rawdata = self.rawdata + bindata
        return self.unpackData(bindata)

    def write(self, fh):
        """
        Read the packed data header from the file handler
        :param fhdl: The file handler
        :return: True if unpacking is OK, False otherwise
        """
        try:
            self.rawdata = self.pack()
            fh.write(self.rawdata)
        except Exception as excpt:
            raise
            return False
        return True

    def info(self):
        """
        Show the header information in a nice way
        :return: -
        """
        print(('-' * 60) + '\n' +
              ('Space_Wire_Packet_Header: {}\n' +
               'Operation_Id (SOC Id)     {:010d}\n' +
               'CCD-ID Col/Row:           {}\n' +
               'Data Length:              {} bytes\n' +
               'CRC_16 Hdr:               {}\n' +
               'CRC_16 Data:              {}\n' +
               'Space_Wire_Packet_Footer: {}\n' +
               '{} bytes\n').\
              format(self.spaceWirePcktHdr,
                     self.operationId.data,
                     self.ccdId,
                     self.dataLength,
                     self.crc16Hdr,
                     self.crc16Data,
                     self.spaceWirePcktFtr,
                     self.size) +
              ('-' * 60))


class LE1VISProduct:
    """
    Class LE1VISProduct

    LE1 VIS Product, based on ICD 4.0 draft 9
    """
    def __init__(self):
        pass


def read_4_byte_word(fhdl):
    """
    Read 4 byte word from file, and get back to the starting position
    :param fhdl: The file handler
    :return: the 4 byte word as an integer
    """
    buffer = fhdl.read(4)
    if buffer == b'':
        return -1
    fourbyte = unpack('>I', buffer)[0]
    fhdl.seek(-4, 1)
    return fourbyte


def main():
    pass


if __name__ == '__main__':
    main()
