#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
basic.py

Basic types and classes for LE1 Data structures
"""
#----------------------------------------------------------------------

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

# System
import os
import sys
import logging

from struct import Struct
#from pprint import pprint

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

class Encoded(Struct):
    """
    Class Encoded

    Class derived from Struct that serves as base to elements that can be simply
    packed/unpacked with the Struct API
    """
    def __init__(self, name, fmt=">I", nbytes=4):
        """
        Initialize class instance
        """
        self.name = name
        self.nbytes = nbytes
        self.fmt = fmt
        self.pck = Struct(fmt)
        self.binstr = None
        self.bindata = None
        self.data = None

    def set(self, value):
        """
        Set the internal data value
        """
        self.data = value
        self.bindata = value

    def pack(self):
        """
        Pack the internal data value
        :return: The packed binary string
        """
        if len(self.bindata) > 1:
            self.binstr = self.pck.pack(*(self.bindata))
        else:
            self.binstr = self.pck.pack(self.data)
        return self.binstr

    def unpack(self, binstr):
        """
        Unpack from the provided binary string the required data
        :return: The unpacked value
        """
        self.binstr = binstr
        self.bindata = self.pck.unpack(binstr)
        self.data = self.bindata[0]
        return self.data

    def info(self):
        """
        Provides a info string for the underlying variable
        :return: The info string in the form 'name: value'
        """
        return '{}: {}'.format(self.name, str(self.data))

    def __str__(self):
        """
        String representation of the hex. integer
        """
        return '{}'.format(self.data)


def main():
    pass


if __name__ == '__main__':
    main()
