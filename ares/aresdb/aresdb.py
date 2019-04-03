#!/usr/bin/python
# -*- coding: utf-8 -*-
'''aresdb

Package to help in the access to ARES Server local database'''

import os, sys
import re
import time
import glob
import json

import pymysql

VERSION = '0.0.1'

__author__ = "jcgonzalez"
__version__ = VERSION
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Prototype" # Prototype | Development | Production


#----------------------------------------------------------------------------
# Class: AresDBConnection
#----------------------------------------------------------------------------
class AresDBConnection(object):
    '''
    This class contains the basic API that the AresTools use to retrieve information
    from the ARES Server local MySQL database
    '''

    def __init__(self, host=None, port=None, user=None, pwd=None, db=None,
                 connection=None):
        '''
        Instance initialization method
        '''

        # Get DB connection parameters
        if connection:
            self.host = connection['host']
            self.port = connection['port']
            self.user = connection['user']
            self.pwd = connection['pwd']
            self.db = connection['db']
        else:
            if host == None or port == None or user == None or pwd == None or db == None:
                raise Exception('Connection settings not properly specified or missing!')
            self.host = host
            self.port = port
            self.user = user
            self.pwd = pwd
            self.db = db


    def getParamNames(self):
        '''
        Returns a tuple with all the parameter names from the ARES DB
        '''
        connection = pymysql.connect(host = self.host,
                                     port = self.port,
                                     user = self.user,
                                     password = self.pwd,                               
                                     db = self.db,    
                                     cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                query = ("SELECT * FROM DATA_DEFS_TBL")

                cursor.execute(query)

                paramNames = [row['NAME'] for row in cursor]
    
        finally:
            connection.close()

        return paramNames

    
def main():
    '''
    Main processor program
    '''
    importer = AresDBConnection()


if __name__ == "__main__":
    main()
