#!/usr/bin/python
# -*- coding: utf-8 -*-
'''euclid_images

Classes to read VIS CCD data'''

from .euclid_image import ImageType, Euclid_Image, Diagnostic, \
                          assemblePhysCcd, assembleScienceImage
from .constants import VIS
from astropy.io import fits


import numpy as np
import os
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


#----------------------------------------------------------------------------
# Class: VIS_CCD
#----------------------------------------------------------------------------
class VIS_Image(Euclid_Image):
    '''
    Processor is the base class for all the processors to be executed from
    the Euclid QLA Processing Framework, independent if they are run inside or
    outside Docker containers.
    '''

    logger = logging.getLogger(__name__ + '.VIS_Image') #__class__.__name__)
    if not logger.handlers: logger.addHandler(logging.NullHandler())

    def __init__(self, filename=None):
        '''
        Instance initialization method
        '''
        VIS_Image.logger.info("Creating new VIS Image")

        super(VIS_Image, self).__init__(ImageType.Unknown)

        if filename: self.read(filename)

    def read(self, filename):
        '''
        Read a FITS file with a set of VIS images
        :param filename:  Name of the file to read
        :return:
        '''
        logging.debug('Analysing: {}'.format(filename))
        #image_file = get_pkg_data_filename(filename)
        #fits.info(image_file)

        self.hdul = fits.open(filename)

        startHdu = 1 if len(self.hdul) > 1 else 0

        self.num_ext = len(self.hdul) - startHdu
        self.startHdu = startHdu
        self.dims = [hdu.data.shape for hdu in self.hdul[startHdu:]]
        self.headers = [hdu.header for hdu in self.hdul]
        self.imageType = [ImageType.obtain(shape=d) for d in self.dims]
        self.bitpix = [hdu.header['bitpix'] for hdu in self.hdul[startHdu:]]

        try:
            self.bscale = [hdu.header['bscale'] for hdu in self.hdul[startHdu:]]
        except:
            self.bscale = [1 for hdu in self.hdul[startHdu:]]

        try:
            self.bzero = [hdu.header['bzero'] for hdu in self.hdul[startHdu:]]
        except:
            self.bzero = [0 for hdu in self.hdul[startHdu:]]

        #print(self.hdul)
        #print(self.num_ext)
        #print(self.headers)3
        print('ImageType: {}'.format(self.imageType))
        print('Dimensions: {}'.format(self.dims))
        print('Encoding: BitPix={}, BScale={}, BZero={}'.format(self.bitpix,self.bscale,self.bzero))

    def fetch(self, n=0):
        '''
        According to the image type, performs the neccessary splits
        We assume we have only 1 image (ONE 1-quadrant image or ONE 4-quadrant composed CCD image,
        physical or scientifc -- i.e. with pre/post/over scan rows/cols removed)
        '''
        self.num_ccd = 0
        self.num_quadrants = 0

        self.num_phys_ccd = 0
        self.num_phys_quadrants = 0

        self.data = None

        imageType = self.imageType[n]

        if imageType == ImageType.Unknown:
            return
        elif self.imageType == ImageType.QData:     # Data area of a single Quadrant
            self.data = [None,
                         [{'data': self.hdul[self.startHdu+n].data,
                           'bitpix': self.bitpix[n],
                           'bscale': self.bscale[n],
                           'bzero': self.bzero[n]},
                          None,
                          None,
                          None]]
            self.num_quadrants = 1
        elif imageType == ImageType.QPhys:     # Physical area of a single Quadrant
            self.data = [None,
                         [{'data': self.hdul[self.startHdu+n].data[:,VIS.NumOfPrescanCols:-VIS.NumOfOverscanCols],
                           'bitpix': self.bitpix[n],
                           'bscale': self.bscale[n],
                           'bzero': self.bzero[n]},
                          None,
                          None,
                          None]]
            self.num_phys_quadrants = 1
        elif imageType == ImageType.QPhys_:    # Physical area of a single Quadrant, with the postscan rows
            self.data = [None,
                         [{'data': self.hdul[self.startHdu+n].data[:-VIS.NumOfPostscanRows/2, VIS.NumOfPrescanCols:-VIS.NumOfOverscanCols],
                           'bitpix': self.bitpix[n],
                           'bscale': self.bscale[n],
                           'bzero': self.bzero[n]},
                          None,
                          None,
                          None]]
            self.num_phys_quadrants = 1
        elif imageType == ImageType.CcdData:   # Data area of the entire CCD
            #nr, nc = self.dims[n]
            quadrants = self.splitIntoDataQuadrants(n=n, remove_separation_rows=False)
            self.data = [{'data': self.hdul[self.startHdu+n].data,
                           'bitpix': self.bitpix[n],
                           'bscale': self.bscale[n],
                           'bzero': self.bzero[n]},
                         quadrants]
            self.num_quadrants = 4
            self.num_ccd = 1
        elif imageType == ImageType.CcdData_:  # Data area of the entire CCD, with the additional separation rows
            #nr, nc = self.dims[n]
            quadrants = self.splitIntoDataQuadrants(n=n, remove_separation_rows=True)
            self.data = [{'data': self.hdul[self.startHdu+n].data,
                          'bitpix': self.bitpix[n],
                          'bscale': self.bscale[n],
                          'bzero': self.bzero[n]},
                         quadrants]
            self.num_quadrants = 4
            self.num_ccd = 1
        elif imageType == ImageType.CcdPhys:   # Physical area of CCD, prescan and overscan columns included
            #nr, nc = self.dims[n]
            quadrants = self.splitIntoPhysQuadrants(n=n)
            self.data = [{'data': self.hdul[self.startHdu+n].data,
                          'bitpix':                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             self.bitpix[n],
                          'bscale': self.bscale[n],
                          'bzero': self.bzero[n]},
                         quadrants]
            self.num_phys_quadrants = 4
            self.num_phys_ccd = 1
        elif imageType == ImageType.CcdPhys_:  # Physical area of CCD, also with postscan rows
            #nr, nc = self.dims[n]
            quadrants = self.splitIntoPhysQuadrants(n=n)
            quadrants[n]['data'] = quadrants[n]['data'][:-VIS.NumOfPostscanRows/2,:]
            quadrants[1]['data'] = quadrants[1]['data'][:-VIS.NumOfPostscanRows/2,:]
            quadrants[2]['data'] = quadrants[2]['data'][VIS.NumOfPostscanRows/2:,:]
            quadrants[3]['data'] = quadrants[3]['data'][VIS.NumOfPostscanRows/2:,:]
            self.data = [{'data': self.hdul[self.startHdu+n].data,
                          'bitpix': self.bitpix[n],
                          'bscale': self.bscale[n],
                          'bzero': self.bzero[n]},
                         quadrants]
            self.num_phys_quadrants = 4
            self.num_phys_ccd = 1
        else:
            return None

        #ccd = fits.getdata(image_file, ext=0)

        # plt.figure()
        # plt.imshow(ccd, cmap='gray') 
        # plt.colorbar()
        # with open(filename + '.png', 'wb') as figfile:
        #    plt.savefig(figfile, format='png')

    def generateCountHistogram(self, img=None):
        '''
        Generates a histogram of the image counts
        '''
        if not img: return None
        hist = np.zeros(65536)
        #dims = self.dims[img] 
        for row in self.hdul[img + 1].data:
            for cnt in row:
                hist[cnt] = hist[cnt] + 1
        return hist

    def splitIntoPhysQuadrants(self, n=-1):
        if n < 0:
            return None

        shape = self.hdul[n + self.startHdu].shape
        hdu = self.hdul[n + self.startHdu]
        ccd = hdu.data
        print(ccd)

        nrows = shape[0]
        ncols = shape[1]
        nrows_2 = int(nrows / 2)
        ncols_2 = int(ncols / 2)

        return [{'data': ccd[:nrows_2, :ncols_2],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]},
                {'data': ccd[:nrows_2, ncols_2:],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]},
                {'data': ccd[nrows_2:, :ncols_2],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]},
                {'data': ccd[nrows_2:, ncols_2:],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]}]

    def splitIntoDataQuadrants(self, n=-1, remove_separation_rows=True):
        if n < 0:
            return None

        shape = self.hdul[n + self.startHdu].shape
        hdu = self.hdul[n + self.startHdu]
        ccd = hdu.data
        print(ccd)

        nrows = shape[0]
        ncols = shape[1]
        nrows_2 = int(nrows / 2)
        ncols_2 = int(ncols / 2)

        sepr = int(VIS.NumOfSeparationRows / 2) if remove_separation_rows else 0

        return [{'data': ccd[:nrows_2-sepr, :ncols_2],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]},
                {'data': ccd[:nrows_2-sepr, ncols_2:],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]},
                {'data': ccd[nrows_2+sepr:, :ncols_2],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]},
                {'data': ccd[nrows_2+sepr:, ncols_2:],
                 'bitpix': self.bitpix[n],
                 'bscale': self.bscale[n],
                 'bzero': self.bzero[n]}]

    def storeInFile(self, filename):
        logger.info("Storing VIS Image in file {}".format(filename))


def main():
    '''
    Main processor program
    '''
    VISccd = VIS_Image()


if __name__ == "__main__":
    main()
