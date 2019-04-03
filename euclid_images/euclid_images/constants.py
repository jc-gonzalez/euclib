#!/usr/bin/python
# -*- coding: utf-8 -*-
'''euclid_images

Classes to read VIS CCD data'''


VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


#----------------------------------------------------------------------------
# Class: VIS_CCD
#----------------------------------------------------------------------------
class VIS:
    '''
    Processor is the base class for all the processors to be executed from
    the Euclid QLA Processing Framework, independent if they are run inside or
    outside Docker containers.
    '''

    NumOfPrescanCols = 51
    NumOfOverscanCols = 20
    NumOfPostscanRows = 20
    
    NumOfDataColsPerQ = 2048
    NumOfDataRowsPerQ = 2066

    NumOfPhysColsPerQ = NumOfDataColsPerQ + NumOfPrescanCols + NumOfOverscanCols
    NumOfPhysRowsPerQ = NumOfDataRowsPerQ
    NumOfPhysRowsPerQwithPostScan = NumOfDataRowsPerQ + NumOfPostscanRows

    NumOfTotalPhysCols = 2 * NumOfPhysColsPerQ
    NumOfTotalPhysRows = 2 * NumOfPhysRowsPerQ
    NumOfTotalPhysRowswithPostScan = 2 * NumOfPhysRowsPerQwithPostScan

    NumOfTotalDataCols = 2 * NumOfDataColsPerQ
    NumOfTotalDataRows = 2 * NumOfDataRowsPerQ

    NumOfSeparationRows = 4

    NumOfFinalDataCols = NumOfTotalDataCols
    NumOfFinalDataRows = NumOfTotalDataRows + NumOfSeparationRows


def main():
    '''
    Main processor program
    '''
    pass


if __name__ == "__main__":
    main()
