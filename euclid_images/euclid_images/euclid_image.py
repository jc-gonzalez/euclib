#!/usr/bin/python
# -*- coding: utf-8 -*-
'''euclid_image

Base classes for Euclid image data'''

from enum import Enum
from .constants import VIS

import numpy as np
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


#----------------------------------------------------------------------------
# Enum ImageType: Type of image according to its size
#----------------------------------------------------------------------------
class ImageType(Enum):
    Unknown = 0
    QData = 1    # Data area of a single Quadrant
    QPhys = 2    # Physical area of a single Quadrant
    QPhys_ = 3   # Physical area of a single Quadrant, with the postscan rows
    CcdData = 4  # Data area of the entire CCD
    CcdData_ = 5 # Data area of the entire CCD, with the additional separation rows
    CcdPhys = 6  # Physical area of CCD, prescan and overscan columns included
    CcdPhys_ = 7 # Physical area of CCD, also with postscan rows

    @staticmethod
    def obtain(rows=None, cols=None, shape=None):
        if shape:
            rows, cols = shape
        elif (not rows) and (not cols):
            return ImageType.Unknown

        if cols == VIS.NumOfDataColsPerQ:
            return ImageType.QData
        elif cols == VIS.NumOfPhysColsPerQ:
            if rows == VIS.NumOfPhysRowsPerQ:
                return ImageType.QPhys
            elif rows == VIS.NumOfPhysRowsPerQwithPostScan:
                return ImageType.QPhys_
            else:
                return ImageType.Unknown
        elif cols == VIS.NumOfTotalDataCols:
            if rows == VIS.NumOfTotalDataRows:
                return ImageType.CcdData
            elif rows == VIS.NumOfFinalDataRows:
                return ImageType.CcdData_
            else:
                return ImageType.Unknown
        elif cols == VIS.NumOfTotalPhysCols:
            if rows == VIS.NumOfTotalPhysRows:
                return ImageType.CcdPhys
            elif rows == VIS.NumOfTotalPhysRowswithPostScan:
                return ImageType.CcdPhys_
            else:
                return ImageType.Unknown

def assemblePhysCcd(quadrants):
    '''
    Put together in a single array the set of four quadrants.
    They have to be of ImageType.QPhys or QPhys_, and the resulting CCD image
    will be of type ImageType.CcdPhys or CcdPhys_
    The values in q correspond to the Image extension index.  
    For the HDU index, +1 must be added.
    '''
    # Ensure types are correct
    for q in quadrants:
        imgType = ImageType.obtain(shape=q['data'].shape)
        if ((imgType != ImageType.QPhys) and (imgType != ImageType.QPhys_)):
            logger.warning("Cannot assemble the quadrants in images {} into one phys. CCD".format(q))
            return None

    dims = quadrants[0]['data'].shape
    q_rows = dims[0]
    q_cols = dims[1]
    
    ccd_rows = q_rows * 2 
    ccd_cols = q_cols * 2 

    ccd = np.zeros(shape=(ccd_rows, ccd_cols))
    ccd[:q_rows,:q_cols] = quadrants[0]['data'][:, :]
    ccd[:q_rows,q_cols:] = quadrants[1]['data'][:, ::-1]
    ccd[q_rows:,:q_cols] = quadrants[2]['data'][::-1, :]
    ccd[q_rows:,q_cols:] = quadrants[3]['data'][::-1, ::-1]

    return {'data': ccd,
            'bitpix': quadrants[0]['bitpix'],
            'bscale': quadrants[0]['bscale'],
            'bzero': quadrants[0]['bzero']}

def assembleScienceImage(quadrants, separation_rows=True):
    '''
    Put together in a single array the set of four quadrants.
    They have to be of ImageType.QPhys or QPhys_, and the resulting CCD image
    will be of type ImageType.CcdPhys or CcdPhys_
    The values in q correspond to the Image extension index.
    For the HDU index, +1 must be added.
    '''
    # Ensure types are correct
    for q in quadrants:
        imgType = ImageType.obtain(shape=q['data'].shape)
        if (imgType != ImageType.QData):
            logger.warning("Cannot assemble the quadrants in images {} into one Science image".format(q))
            return None

    dims = quadrants[0]['data'].shape
    q_rows = dims[0]
    q_cols = dims[1]

    ccd_rows = q_rows * 2
    ccd_cols = q_cols * 2
    sep_rows = VIS.NumOfSeparationRows if separation_rows else 0

    ccd = np.zeros(shape=(ccd_rows + sep_rows, ccd_cols))

    print(ccd.shape, [quadrants[i]['data'].shape for i in range(4)])

    ccd[:q_rows, :q_cols] = quadrants[0]['data']
    ccd[:q_rows, q_cols:] = quadrants[1]['data']
    ccd[q_rows+sep_rows:, :q_cols] = quadrants[2]['data']
    ccd[q_rows+sep_rows:, q_cols:] = quadrants[3]['data']


    return {'data': ccd,
            'bitpix': quadrants[0]['bitpix'],
            'bscale': quadrants[0]['bscale'],
            'bzero': quadrants[0]['bzero']}


#----------------------------------------------------------------------------
# Class: Euclid_Image
#----------------------------------------------------------------------------
class Euclid_Image:
    '''
    Base class for all imagess (FITS files) read for Euclid
    '''
    __slots__ = ["imageType"]
    def __init__(self, imageType):
        self.imageType = imageType


#----------------------------------------------------------------------------
# Class: Diagnostic
#----------------------------------------------------------------------------
class Diagnostic:
    def __init__(self):
        pass


def main():
    '''
    Main processor program
    '''
    pass


if __name__ == "__main__":
    main()
