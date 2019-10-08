#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
appgui.py

GUI Application class for the Element IO Simulator tool
'''

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

import os, sys
_filedir_ = os.path.dirname(__file__)
_appsdir_, _ = os.path.split(_filedir_)
_basedir_, _ = os.path.split(_appsdir_)
sys.path.insert(0, os.path.abspath(os.path.join(_filedir_, _basedir_)))

from tkinter import *
from tkinter import messagebox as MessageBox
from tkinter import simpledialog as SimpleDialog
from tkinter.colorchooser import askcolor
from tkinter import filedialog
from tkinter import scrolledtext
from tkinter import font as tkFont

from tkinter import ttk

# used to check if functions have a parameter
from inspect import getfullargspec as getArgs

PYTHON2 = False
PY_NAME = "python3"
STRING = str

# import other useful classes
import errno
import time
import datetime
import logging
import argparse
import glob
import shutil

import subprocess
import configparser
import json

from pprint import pprint

from gui.simpleeditor import launch_modal_editor
from gui.gui_elements import EntrySpinbox, YMDSpinboxes, YDoYSpinboxes, \
    HMSmsSpinboxes, DateTime, StatusBar, CustomText

from tools.filetools import getContentOfFile, createDirIfNotExist, runCommandAsSubprocess

# details
__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = "0.0.2"
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""

class LoggingHandlerFrame(ttk.Frame):

    class Handler(logging.Handler):
        def __init__(self, widget):
            logging.Handler.__init__(self)
            self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s")) #%(asctime)s: %(message)s"))
            self.widget = widget
            self.widget.config(state='disabled')
            self.widget.config(state='disabled')
            self.widget.tag_config("INFO", foreground="black")
            self.widget.tag_config("DEBUG", foreground="darkgrey")
            self.widget.tag_config("WARNING", foreground="magenta")
            self.widget.tag_config("ERROR", foreground="red")
            self.widget.tag_config("CRITICAL", foreground="darkred", underline=1)
            self.red = self.widget.tag_configure("red", foreground="red")

        def emit(self, record):
            self.widget.config(state='normal')
            self.widget.insert(END, self.format(record) + "\n", record.levelname)
            self.widget.see(END)  # Scroll to the bottom
            self.widget.config(state='disabled') 
            self.widget.update() # Refresh the widget)
        
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self.scrollbar = Scrollbar(self)
        self.scrollbar.grid(row=0, column=1, sticky=(N,S,E))

        self.text = Text(self, yscrollcommand=self.scrollbar.set)
        self.text.grid(row=0, column=0, sticky=(N,S,E,W))

        self.scrollbar.config(command=self.text.yview)

        self.logging_handler = LoggingHandlerFrame.Handler(self.text)

    def appendHandlerToLogger(self, theLogger):
        theLogger.addHandler(self.logging_handler)
        
class FlashableLabel(ttk.Label):
    def change(self, txt, fg, bg, count):
        self.oldbg = self.cget('background')
        self.oldfg = self.cget('foreground')
        self.configure(text=txt, background=bg, foreground=fg)
        self.flash(count)
        
    def flash(self, count):
        bg = self.cget('background')
        fg = self.cget('foreground')
        self.configure(background=fg, foreground=bg)
        count += 1
        if (count < 16):
             self.after(300, self.flash, count)
        else:
            self.configure(text='', background=self.oldbg, foreground=self.oldfg)
             
class App:
    '''
    Main application class for the GUI
    '''

    def __init__(self, parent, args, logger):
        '''
        Initialize the class data members and build the entire GUI
        '''
        self.parent = parent
        self.logger = logger

        self.dataDir = args.data_dir
        self.dataFiles = [os.path.basename(f) for f in glob.glob(args.data_dir + '/*')]
        self.recvFolder = args.incoming_dir
        
        self.targetPairs = [p.split(':') for p in args.outgoing_dirs.split(',')]
        self.targetList = tuple(p[0] for p in self.targetPairs)
        self.targetDirs = {p[0]: p[1] for p in self.targetPairs}
        
        #=== Variables

        self.retrToPid = StringVar()
        self.retrToPid.set(100)

        self.retrPidBlk = StringVar()
        self.retrPidBlk.set(10)

        parent.title('{} I/O Simulation Tool'.format(args.element))

        # GUI frames
        frmSend = ttk.LabelFrame(parent, text='Send data files to other systems')
        frmRecv = ttk.LabelFrame(parent, text='Received data files')
        frmLog = ttk.LabelFrame(parent, text='Log info')

        #-- Title
        lblTitle = ttk.Label(parent, text='{} I/O Simulation Tool'.format(args.element),
                             font=('Arial Bold', 16))
        lblTitle.pack(side=TOP, anchor=W, padx=5, pady=5)

        #-- First frame: send
        frmSend.pack(side=TOP, fill=X, padx=1, pady=1)
        self.dataFilesList = StringVar(value=self.dataFiles)
        self.dataFilesListBox = Listbox(frmSend, listvariable=self.dataFilesList,
                                        height=6)
        self.dataFilesListBox.pack(side=LEFT, expand=YES, fill=X, padx=5, pady=5)
        
        frmSendR = ttk.Frame(frmSend)
        frmSendR.pack(side=LEFT, expand=NO, padx=5, pady=5)

        frmSendUR = ttk.Frame(frmSendR)
        frmSendUR.pack(side=TOP, expand=NO, padx=5, pady=5)

        frmSendDR = ttk.Frame(frmSendR)
        frmSendDR.pack(side=TOP, expand=NO, padx=5, pady=5)

        self.lblSend = FlashableLabel(frmSendDR, text='')
        self.lblSend.pack(padx=20)

        self.btnSend = ttk.Button(frmSendUR, text="Send =>", command=self.send)
        self.btnSend.pack(side=LEFT, expand=NO, fill=X, padx=20)

        self.toElem = StringVar()
        self.toElemCBox = ttk.Combobox(frmSendUR, textvariable=self.toElem, width=6)
        self.toElemCBox['values'] = self.targetList
        self.toElemCBox.pack(side=LEFT, expand=NO, fill=X, padx=5)

        #-- Second frame: receive
        frmRecv.pack(side=TOP, fill=X, padx=1, pady=1)
        
        self.recvFiles = []
        self.recvFilesList = StringVar()
        self.recvFilesListBox = Listbox(frmRecv, listvariable=self.recvFilesList,
                                        height=6)
        self.recvFilesListBox.pack(side=LEFT, expand=YES, fill=X, padx=5, pady=5)

        self.lblRecv = FlashableLabel(frmRecv, text='')
        self.lblRecv.pack(side=LEFT, padx=20)

        #-- Third frame: log
        frmLog.pack(side=TOP, fill=X, padx=1, pady=1)        
        #self.log = Text(frmLog, height=16)
        self.log = LoggingHandlerFrame(frmLog)
        self.log.appendHandlerToLogger(self.logger)
        self.log.pack(side=TOP, fill=BOTH, anchor=W, padx=5, pady=5)

        #-- Finally, a status bar

        status = StatusBar(parent)
        status.pack(side=BOTTOM, fill=X)
        status.set("Loaded.")

        self.logger.info('Starting...')

        self.parent.after(1000, self.recv)
        
    def send(self):
        fileno = self.dataFilesListBox.curselection()
        if not fileno: return

        tgt = self.toElemCBox.get()
        if not tgt: return

        filename = self.dataFiles[fileno[0]]
        fullfile = os.path.join(self.dataDir, filename)
        tgtFolder = self.targetDirs[tgt]
        self.logger.info('Sending file {} to {} ...'.format(filename, tgt))
        self.logger.debug('Moving file {} to folder {} ...'\
                          .format(fullfile, tgtFolder))                    
        if filename and tgt:
            self.lblSend.change('SENDING', 'yellow', 'blue', 0)
            shutil.move(fullfile, tgtFolder)
            self.dataFiles.remove(filename)
            self.dataFilesList.set(self.dataFiles)
            
    def recv(self):
        currList = glob.glob(self.recvFolder + '/*')
        newList = []
        for item in currList:
            filename = os.path.basename(item)
            if filename not in self.recvFiles:
                newList.append(item)
                
        if len(newList) > 0:
            self.lblRecv.change('RECEIVING', 'yellow', 'red', 0)
            for item in newList:
                filename = os.path.basename(item)
                self.recvFiles.append(filename)
                self.logger.info('File received: {}'.format(filename))
                self.logger.info('New incoming file {}'.format(item))
            self.recvFilesList.set(self.recvFiles)
            
        self.parent.after(1000, self.recv)
                            
    def quit(self):
        '''
        Quit the application
        '''
        self.logger.info('Quitting.')
        self.parent.destroy()


if __name__ == '__main__':
    print('This is a library class and cannot be executed.')
    sys.exit()
