#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oss_reader.py

Parse and select data from an OSS XML file

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

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from collections import OrderedDict as odict
from astropy.io import fits
import numpy as np

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

class OSS:
    """
    Class OSS

    Parse and read to memory an OSS XML file
    """
    def __init__(self, file):
        """
        Initialize class
        :param file: OSS file to read (in XML)
        """
        self.ossFileName = file
        self.survey = None

    def read(self):
        """
        Parses XML file and reads its content
        :return: True on success
        """
        try:
            # Open XML document using minidom parser
            self.tree = ET.parse(self.ossFileName)
            self.root = self.tree.getroot()
            return True #self.root.tag == 'OperationalSurvey'
        except:
            logger.error(f'Cannot parse XML OSS file {self.ossFileName}')
            return False

    def getObs(self, obsid):
        """
        Return the content of an observation with a given ID, in the form of a
        disctionary
        :param id: the observation id
        :return: None if failed, the obs. node otherwise
        """
        obs_node = self.root.findall("./Observation/[@id='{}']".format(obsid))[0]
        if obs_node == []:
            return None
        return self.nodeToDict(node=obs_node)

    def nodeToDict(self, node=None):
        """
        Function to add the childs of a node as entries in a dictionary
        :param dct: the dictionary for the node
        :param node: the DOM node
        :return: the dictionary
        """
        itemsInLists = []

        dct = odict()
        for child in node:
            #print('{}: {}'.format(child.tag, child.text))
            newItem = odict()
            if not child.text is None:
                newItem['text'] = child.text
            if len(child.attrib) > 0:
                dcta = odict()
                for attrname, attrvalue in child.attrib.items():
                    dcta[attrname] = attrvalue
                newItem['attribs'] = dcta
            if len(child) > 0:
                newItem['children'] = self.nodeToDict(node=child)

            tg = child.tag
            if tg in dct:
                tgl = tg + '_list'
                if not tgl in dct:
                    dct[tgl] = [dct[tg]]
                    itemsInLists.append(tg)
                dct[tgl].append(newItem)
            else:
                dct[tg] = newItem

        for tg in itemsInLists:
            x = dct.pop(tg)

        return dct

    def dictToTable(self, dct=None, prefix=''):
        """
        Function to add the childs of a node as entries in a dictionary
        :param dct: the dictionary for the node
        :param prefix: prefix to build hierarchy
        :return: the list of lines of the table
        """
        tbl = []

        for k,v in dct.items():

            #print('k={}\nv={}\n'.format(k,v))

            name = prefix + k

            if type(v) == list:
                i = 1
                for item in v:
                    nk = '{}.{}'.format(k[:-5],i)
                    tbl.extend(self.dictToTable(dct={nk: item},
                                                prefix=prefix))
                    i = i + 1
                continue

            # text
            if 'text' in v:
                text = v['text'].replace(' ', '').replace('\n','')
                if not text is None:
                    if len(text) > 0:
                        newit = [name, text]
                        tbl.append(newit)
                        #print(newit)

            # atribs
            if 'attribs' in v:
                for ak,av in v['attribs'].items():
                    newit = [name + ':' + ak, av]
                    tbl.append(newit)
                    #print(newit)

            # children
            if 'children' in v:
                tbl.extend(self.dictToTable(dct=v['children'],
                                            prefix=name + '.'))

        return tbl

    def addTableToFits(self, file=None, obstable=None,
                       colspec=[('ITEM', '40A'), ('VALUE', '30A')]):
        """
        Add Binary Table extension to existing FITS file
        :param file: The FITS file name
        :param table: The table to append
        :param colspec; THe names and format to use for the columns
        :return: True upon success, False otherwise
        """
        if not file:
            logger.error('FITS file name not provided')
            return False
        if not obstable:
            logger.error('Table with observation metadata not provided')
            return False
        if type(colspec) != list:
            logger.error('Cols.spec "colspec" must be a list of 2-element tuples ' + \
                         ' [(name1, fmt1), ...]')
            return False

        # Columns definition
        cols = []
        i = 0
        for colsp in colspec:
            colname, colfmt = colsp
            cols.append(fits.Column(name=colname, format=colfmt,
                                    array=np.asarray([x[i] for x in obstable])))
            i = i + 1

        try:
            hdu = fits.BinTableHDU.from_columns(cols)
        except:
            logger.error('Could not create the obs. info table')
            return False

        try:
            with fits.open(file, mode='update') as hdul:
                hdul.append(hdu)
                hdul.flush()
        except:
            logger.error(f'Could not append the obs. info table to the file {file}')
            return False

        return True

    def addObsDataToFits(self, file=None, obsid=None):
        """
        Looks for obs. data in a OSS file, and stores a table with these data in
        a FITS file.
        :param file: The file name of the FITS to include the new obs. data
        :param obsid: The obs.id
        :return: True upon success, False otherwise
        """
        obs = None
        try:
            if not self.read():
                logger.error(f'Cannot read XML OSS file {self.ossFileName}')
                return False
        except:
            logger.error(f'Error reading obs.id information from OSS XML file')
            return False

        obs = self.getObs(obsid)
        if not obs:
            logger.error(f'Cannot find information of obs.id = {obsid}')
            return False

        obsTable = []
        try:
            obsTable = self.dictToTable(dct=obs)
            obsTable.insert(0, ['ObsId', str(obsid)])
        except:
            logger.error('Cannot create obs. info. table')
            return False

        try:
            # Append bintable extension with obs. info table for FITS file
            self.addTableToFits(file=file, obstable=obsTable)
        except:
            logger.error('Cannot add obs.id. information to file')
            return False

        return True


def main():
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname).1s ' +
                                             '%(name)s %(module)s:%(lineno)d %(message)s',
                                             datefmt='%y-%m-%d %H:%M:%S'))
    logger.addHandler(c_handler)

    ffile = '/Users/jcgonzalez/Desktop/new1.fits'

    oss = OSS('/Users/jcgonzalez/Desktop/osstest.xml')
    logger.info('New OSS object created')

    if oss.addObsDataToFits(file=ffile, obsid=23):
        logger.info(f'New table appended to FITS file {ffile}')
    else:
        logger.warn('Could not add new obs.id. info table to file')


if __name__ == '__main__':
    main()
