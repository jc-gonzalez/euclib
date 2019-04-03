#!/usr/bin/python
# -*- coding: utf-8 -*-
'''test_vis_images.py

Classes to read VIS CCD data'''

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from euclid_images.euclid_images.vis_image import VIS_Image

from astropy.io import fits
import numpy as np

import logging
logger = logging.getLogger()

VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


def configureLogs():
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('file.log')
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s %(levelname).1s %(name)s %(module)s:%(lineno)d %(message)s',
                                 datefmt='%y-%m-%d %H:%M:%S')
    f_format = logging.Formatter('{asctime} {levelname:4s} {name:s} {module:s}:{lineno:d} {message}',
                                 style='{')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    lmodules = os.environ['LOGGING_MODULES'].split(':')
    for lname in reversed(lmodules):
        lgr = logging.getLogger(lname)
        if not lgr.handlers:
            lgr.addHandler(c_handler)
            lgr.addHandler(f_handler)


def main():
    '''
    Main processor program
    '''
    
    # Configure logging system
    configureLogs()

    VISccd = VIS_Image()

    folder = os.path.dirname(os.path.realpath(sys.argv[0])) + '/../data/'

    for f in ['CCD_final.fits',
              'Q0_x0_y0_d1.fits',
              'Q1_x0_y0_d1.fits',
              'Q2_x0_y0_d1.fits',
              'Q3_x0_y0_d1.fits'
              ]:

        logger.info('Reading file {} . . .'.format(folder + f))

        VISccd.read(folder + f)
        VISccd.fetch()

        logger.info('Data: {}'.format(VISccd.data))
        logger.info('CCDs/Phys: {}/{}   Quadrants/Phys: {}/{}'.format(VISccd.num_ccd,
                                                                      VISccd.num_phys_ccd,
                                                                      VISccd.num_quadrants,
                                                                      VISccd.num_phys_quadrants))

        #hist = [[0], [0], [0], [0]]
        #for i in range(4):
        #    hist[i] = VISccd.generateCountHistogram(i)
        #
        #with open('new1.dat', 'w') as fout:
        #    for i in range(0, 65536):
        #        fout.write('{} {} {} {} {}\n'.format(i, hist[0][i], hist[1][i], hist[2][i], hist[3][i]))

        #  tstnum=2
#
        #  if tstnum == 1:
        #      quadrants = VISccd.splitIntoPhysQuadrants(n=0)
        #      print(quadrants)
        #      ccd = assemblePhysCcd(quadrants)
        #      print(ccd['data'].shape)
        #      hdu = fits.PrimaryHDU(ccd['data'])
        #      hdu.scale('int16', bzero=ccd['bzero'], bscale=ccd['bscale'])
        #      hdul = fits.HDUList([hdu])
        #      hdul.writeto('new1.fits')
#
        #  if tstnum == 2:
        #      quadrants = VISccd.splitIntoDataQuadrants(n=0)
        #      print(quadrants)
        #      i = 1
        #      for q in quadrants:
        #          hdu = fits.PrimaryHDU(np.int16(q['data']))
        #          #hdu.scale('int16', bzero=q['bzero'], bscale=q['bscale'])
        #          hdul = fits.HDUList([hdu])
        #          hdul.writeto('newq-{}.fits'.format(i))
        #          i = i + 1
#
        #      ccd = assembleScienceImage(quadrants)
        #      hdu = fits.PrimaryHDU(np.int16(ccd['data']))
        #      #hdu.scale('int16', bzero=ccd['bzero'], bscale=ccd['bscale'])
        #      hdul = fits.HDUList([hdu])
        #      hdul.writeto('newccd.fits')


if __name__ == "__main__":
    main()
