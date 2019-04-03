#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''filetools.py

Handy functions with some file-related utilities
'''

# import other useful classes
import os, sys, errno
import subprocess

# details
__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = "0.1"
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""

def getContentOfFile(file=None):
    '''
    Gets the content of a text file
    '''
    if os.path.exists(file) and os.path.isfile(file):
        with open(file, 'r') as f:
            return f.read()
    else:
        return ''

def run(command):
    '''
    Executes a command and returns the list of lines in stdout
    '''
    #process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    #while True:
    #    line = process.stdout.readline() #.rstrip()
    #    if not line:
    #        break
    #    yield line.decode('utf-8')

    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

def createDirIfNotExist(the_dir=None):
    '''
    Creates a directory if it does not yet exist
    '''
    if the_dir:
        if not os.path.exists(the_dir):
            try:
                os.makedirs(the_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise


if __name__ == '__main__':
    print('This is a library class and cannot be executed.')
    sys.exit()
