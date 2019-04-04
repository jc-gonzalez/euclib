#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
appgui.py

GUI Application class for the Ares Retrieval/Import Tool
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

import subprocess
import configparser
import json

from gui.simpleeditor import launch_modal_editor
from gui.gui_elements import EntrySpinbox, YMDSpinboxes, YDoYSpinboxes, \
    HMSmsSpinboxes, DateTime, StatusBar, CustomText
from ares.aresdb.aresdb import AresDBConnection
from ares.ares_import.ares_import import Importer
from ares.ares_retrieve.ares_retrieve import Retriever

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


RetrievalConfigFile = _basedir_ + '/cfg/retrieval_config.ini'
ImportConfigFile    = _basedir_ + '/cfg/import_config.json'

class App:
    '''
    Main application class for the GUI
    '''

    def __init__(self, parent):
        '''
        Initialize the class data members and build the entire GUI
        '''
        self.parent = parent

        self.readConfig()

        self.db = AresDBConnection(connection = self.cfgData['db'])

        self.paramNames = self.db.getParamNames()

        #=== Variables

        self.from_pid, self.to_pid, self.pids_step = (0, 0, 0)
        self.retrieval_params = {}

        self.retrieveConfigFile = StringVar()
        self.retrieveConfigFile.set(RetrievalConfigFile)

        self.importConfigFile = StringVar()
        self.importConfigFile.set(ImportConfigFile)

        self.retrFromPid = StringVar()
        self.retrFromPid.set(1)

        self.retrToPid = StringVar()
        self.retrToPid.set(100)

        self.retrPidBlk = StringVar()
        self.retrPidBlk.set(10)

        self.retrieveConfigFileContent = getContentOfFile(file=self.retrieveConfigFile.get())
        self.importConfigFileContent = getContentOfFile(file=self.importConfigFile.get())
        self.importRegisteredDataTypes = list(json.loads(self.importConfigFileContent).keys())

        parent.title('ARES Import & Retrieval Tool')

        #=== Dialog menu bar

        menu = Menu(parent)
        parent.config(menu=menu)

        filemenu = Menu(menu)
        menu.add_cascade(label='File', menu=filemenu)
        #filemenu.add_command(label='New', command=self.menuCallback)
        #filemenu.add_command(label='Open...', command=self.menuCallback)
        #filemenu.add_separator()
        filemenu.add_command(label='Quit', command=self.quit)

        helpmenu = Menu(menu)
        menu.add_cascade(label='Help', menu=helpmenu)
        helpmenu.add_command(label='Help...', command=self.help)
        helpmenu.add_separator()
        helpmenu.add_command(label='About...', command=self.about)

        #=== Main GUI structure - notebook

        self.notebook = ttk.Notebook(parent, name='notebook')

        #======================================================================
        #=== 1 - Retrieval from ARES
        #======================================================================

        # Tab 0 - Retrieve from ARES
        tab0 = ttk.Frame(self.notebook)
        self.notebook.add(tab0, text='Retrieve from ARES')
        self.notebook.pack(fill='both', expand=Y, side='top', padx=2, pady=2)

        #----- First section - Show config file name
        frm11 = ttk.Frame(tab0)
        ttk.Label(frm11, text='Applicable retrieval config. file:').pack(side=LEFT, padx=2, pady=2)
        self.retrCfgFileShow = ttk.Entry(frm11, textvariable=self.retrieveConfigFile,state='readonly')
        self.retrCfgFileShow.pack(side=LEFT, expand=1, fill=X, padx=2, pady=2)

        #----- Second section - Retrieval parameters

        lfrm11 = ttk.LabelFrame(tab0, text='Retrieval parameters')

        self.parNamesList = StringVar(value=self.paramNames)

        self.paramRqstMode = StringVar()

        rbtnPar0 = ttk.Radiobutton(lfrm11, text='Select parameter names',
                                   command=self.selectParamNames,
                                   variable=self.paramRqstMode, value='name')
        rbtnPar0.grid(row=0, column=0, padx=10, pady=6)

        rbtnPar1 = ttk.Radiobutton(lfrm11, text='Select range of Param.IDs.',
                                   command=self.selectParamIds,
                                   variable=self.paramRqstMode, value='pid')
        rbtnPar1.grid(row=0, column=1, padx=10, pady=6)

        frm111 = ttk.Frame(lfrm11)
        frm112 = ttk.Frame(lfrm11)

        self.lstParamNames = Listbox(frm111, listvariable=self.parNamesList,
                                     height=10, selectmode='extended')
        self.lstParamNames.pack(side=LEFT, fill=BOTH, expand=Y)

        scrollParName = ttk.Scrollbar(frm111, orient="vertical")
        scrollParName.config(command=self.lstParamNames.yview)
        scrollParName.pack(side=RIGHT, fill=Y)

        self.lstParamNames.config(yscrollcommand=scrollParName.set)

        self.spbxFromPid = EntrySpinbox(frm112, label='From Param Id.:', first=1, last=50000)
        self.spbxFromPid.set(self.retrFromPid.get())
        self.spbxFromPid.pack(fill=X, expand=N)

        self.spbxToPid = EntrySpinbox(frm112, label='To Param Id.:', first=1, last=50000)
        self.spbxToPid.set(self.retrToPid.get())
        self.spbxToPid.pack(fill=X, expand=N)

        self.spbxPidsBlock = EntrySpinbox(frm112, label='Param. Ids. block size (for FITS files)',
                                          first=1, last=50000)
        self.spbxPidsBlock.set(self.retrPidBlk.get())
        self.spbxPidsBlock.pack(fill=X, expand=N)
        ttk.Label(frm112, text=' ').pack(fill=BOTH, expand=Y)

        frm111.grid(row=1, column=0, padx=20, pady=4, sticky=N)
        frm112.grid(row=1, column=1, padx=20, pady=4, sticky=N)

        self.paramRqstMode.set('name')
        self.selectParamNames()

        #----- Third section - Date range

        lfrm12 = ttk.LabelFrame(tab0, text='Date range')

        ttk.Label(lfrm12, text='From timestamp:').grid(row=0, column=0, padx=2, pady=2, sticky=N+W)
        self.fromDateTime = DateTime(lfrm12)
        self.fromDateTime.grid(row=0, column=1, padx=2, pady=10)

        ttk.Button(lfrm12, text='=', command=self.equalFromTo, width=1).grid(row=0, column=2, padx=10, sticky=E)

        ttk.Label(lfrm12, text='To timestamp:').grid(row=1, column=0, padx=2, pady=2, sticky=N+W)
        self.toDateTime = DateTime(lfrm12)
        self.toDateTime.grid(row=1, column=1, padx=2, pady=10)

        #----- Fourth section - button to activate the process

        frm12 = ttk.Frame(tab0)
        ttk.Button(frm12, text=' Retrieve data ', command=self.retrieveData).pack(side=RIGHT)

        #----- Last section - text box to show output

        self.retrOut = Text(tab0)

        #----- Complete packing

        frm11.pack(side=TOP, fill=X, expand=N, padx=2, pady=2)
        lfrm11.pack(fill=BOTH, expand=N, padx=6, pady=6)
        lfrm12.pack(fill=BOTH, expand=N, padx=6, pady=6)
        frm12.pack(fill=BOTH, expand=N, padx=10, pady=10)
        self.retrOut.pack(side=BOTTOM, expand=Y, fill=BOTH)
        self.retrOut.pack_forget()

        #======================================================================
        #=== 2 - Import into ARES
        #======================================================================

        # Tab 1 - Import into ARES
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="Import into ARES")
        self.notebook.pack(fill='both', expand=Y, side='top')

        #self.notesBox = Text(tab1, wrap=WORD, width=40, height=10)
        #vscroll = ttk.Scrollbar(tab1, orient=VERTICAL, command=self.notesBox.yview)
        #self.notesBox['yscroll'] = vscrol.setl
        #vscroll.pack(side=RIGHT, fill=Y)

        #self.notesBox.pack(fill=BOTH, expand=Y, padx=2, pady=2)

        #----- First section - Show config file name
        frm21 = ttk.Frame(tab1)
        ttk.Label(frm21, text='Applicable import config. file:').pack(side=LEFT, padx=2, pady=2)
        self.imprtCfgFileShow = ttk.Entry(frm21, textvariable=self.importConfigFile,state='readonly')
        self.imprtCfgFileShow.pack(side=LEFT, expand=1, fill=X, padx=2, pady=2)

        #----- Second section - Input data

        lfrm21 = ttk.LabelFrame(tab1, text='Input data source')

        self.inputMode = StringVar()
        self.inputDir = StringVar()
        self.inputFiles = StringVar()

        frm211 = ttk.Frame(lfrm21)
        frm212 = ttk.Frame(lfrm21)
        frm213 = ttk.Frame(lfrm21)

        rbtnInp0 = ttk.Radiobutton(frm211, text='Input directory', command=self.useInputDir,
                                   variable=self.inputMode, value='dir', width=14)
        rbtnInp0.pack(side=LEFT, padx=10, pady=2, expand=Y, fill=X)
        self.edInputDir = ttk.Entry(frm211, textvariable=self.inputDir)
        self.edInputDir.pack(side=LEFT, padx=2, pady=2, expand=Y, fill=X)
        ttk.Button(frm211, text='...', command=self.setInputDir, width=2)\
            .pack(side=RIGHT, padx=2, pady=2)
        frm211.pack(expand=Y, fill=X)

        rbtnInp1 = ttk.Radiobutton(frm212, text='Input files', command=self.useInputFiles,
                                   variable=self.inputMode, value='files', width=14)
        rbtnInp1.pack(side=LEFT, padx=10, pady=2, expand=Y, fill=X)
        self.edInputFiles = ttk.Entry(frm212, textvariable=self.inputFiles)
        self.edInputFiles.pack(side=LEFT, padx=2, pady=2, expand=Y, fill=X)
        ttk.Button(frm212, text='...', command=self.setInputFiles, width=2)\
            .pack(side=RIGHT, padx=2, pady=2)
        frm212.pack(expand=Y, fill=X)

        self.inputMode.set('dir')

        self.paramImpFolder = StringVar()

        ttk.Label(frm213, text="Parameter import folder (optional): ")\
           .pack(side=LEFT, padx=10, pady=2)
        #self.edParImportFolder = ttk.Entry(frm213, textvariable=self.paramImpFolder)
        #self.edParImportFolder.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=2)
        self.cboxParamDataType = ttk.Combobox(frm213, textvariable=self.paramImpFolder)
        self.cboxParamDataType.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=2)
        frm213.pack(expand=Y, fill=X)

        #----- Third section - ARES Runtime folder

        lfrm22 = ttk.LabelFrame(tab1, text='ARES Runtime directory')

        self.aresRunTime = StringVar()
        if 'ARES_RUNTIME' in os.environ:
            self.aresRunTime.set(os.environ['ARES_RUNTIME'])
            self.cfgData['ares_runtime'] = self.aresRunTime.get()
            self.writeConfig()
        else:
            self.aresRunTime.set(self.cfgData['ares_runtime'])

        self.edAresRunTime = ttk.Entry(lfrm22, textvariable=self.aresRunTime)
        self.edAresRunTime.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=2)
        ttk.Button(lfrm22, text='...', command=self.setAresRunTime, width=2)\
            .pack(side=RIGHT, padx=2, pady=2)

        self.aresRunTime.trace("w", lambda name, index, mode, sv=self.aresRunTime: self.onChangedRunTime(sv))
        self.onChangedRunTime(self.aresRunTime)

        #----- Fourth section - Parameter descriptions

        lfrm23 = ttk.LabelFrame(tab1, text='New parameter description')

        frm231 = ttk.Frame(lfrm23)
        frm232 = ttk.Frame(lfrm23)

        self.useParamDescripFile = StringVar()
        self.descFile = StringVar()

        chkUseDescFile = ttk.Checkbutton(frm231, text="Use parameter description file",
	                                 command=self.changedUseParamDescFile,
                                         variable=self.useParamDescripFile,
                                         onvalue='yes', offvalue='no')
        chkUseDescFile.pack(side=LEFT, pady=2, padx=6)
        frm231.pack(expand=Y, fill=X)

        ttk.Label(frm232, text="Description file: ")\
           .pack(side=LEFT, padx=14, pady=2)
        self.edDescripFile = ttk.Entry(frm232, textvariable=self.descFile)
        self.edDescripFile.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=2)
        ttk.Button(frm232, text='...', command=self.setDescripFile, width=2)\
            .pack(side=RIGHT, padx=2, pady=2)
        frm232.pack(expand=Y, fill=X)

        self.useParamDescripFile.set('no')
        self.changedUseParamDescFile()

        #----- Fifth section - Import data type

        lfrm24 = ttk.LabelFrame(tab1, text='Import data types')

        frm241 = ttk.Frame(lfrm24)
        frm242 = ttk.Frame(lfrm24)

        self.useSameParamDataType = StringVar()
        self.paramDataType = StringVar()

        chkUseSameParamDataType = ttk.Checkbutton(frm241, text="Assume same data type for all import data files",
	                                          command=self.changedUseSameParamDataType,
                                                  variable=self.useSameParamDataType,
	                                          onvalue='yes', offvalue='no')
        chkUseSameParamDataType.pack(side=LEFT, pady=2, padx=6)
        frm241.pack(expand=Y, fill=X)

        ttk.Label(frm242, text="Parameter data type: ")\
           .pack(side=LEFT, padx=14, pady=2)
        self.cboxParamDataType = ttk.Combobox(frm242, textvariable=self.paramDataType)
        self.cboxParamDataType.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=2)
        self.cboxParamDataType['values'] = self.importRegisteredDataTypes
        frm242.pack(expand=Y, fill=X)

        self.useSameParamDataType.set('no')
        self.changedUseSameParamDataType()

        #----- Sixth section - button to activate the process

        frm22 = ttk.Frame(tab1)
        ttk.Button(frm22, text=' Import data ', command=self.importData).pack(side=RIGHT)

        #----- Last section - text box to show output

        self.imprtOut = Text(tab1)

        #----- Complete packing

        frm21.pack(side=TOP, fill=X, expand=N, padx=2, pady=2)
        lfrm21.pack(fill=BOTH, expand=N, padx=6, pady=6)
        lfrm22.pack(fill=BOTH, expand=N, padx=6, pady=6)
        lfrm23.pack(fill=BOTH, expand=N, padx=6, pady=6)
        lfrm24.pack(fill=BOTH, expand=N, padx=6, pady=6)
        frm22.pack(fill=BOTH, expand=N, padx=10, pady=10)
        self.imprtOut.pack(side=BOTTOM, expand=Y, fill=BOTH)
        self.imprtOut.pack_forget()

        #======================================================================
        #=== 3 - Configuration
        #======================================================================

        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="Configuration files")
        self.notebook.pack(fill='both', expand=Y, side='top')

        #----- 3.1 Retrieval configuration

        lfrm31 = ttk.LabelFrame(tab2, text='Retrieval configuration')

        frm311 = ttk.Frame(lfrm31)
        self.showRetrCfgFileName = ttk.Entry(frm311, textvariable=self.retrieveConfigFile)
        self.showRetrCfgFileName.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=6)
        ttk.Button(frm311, text='...', command=self.setRetrCfgFileName, width=2)\
           .pack(side=RIGHT, padx=2, pady=6, expand=N)

        frm312 = ttk.Frame(lfrm31)
        self.txtRetrCfg = Text(frm312, wrap=WORD, width=40, height=10)
        vscroll1 = ttk.Scrollbar(frm312, orient=VERTICAL, command=self.txtRetrCfg.yview)
        self.txtRetrCfg['yscroll'] = vscroll1.set
        vscroll1.pack(side=RIGHT, fill=Y)
        self.txtRetrCfg.pack(fill=BOTH, expand=Y, padx=2, pady=2)

        self.txtRetrCfg.insert(END, self.retrieveConfigFileContent)

        frm311.pack(side=TOP, expand=N, fill=X, padx=6, pady=6)
        frm312.pack(expand=Y, fill=BOTH, ipadx=10, ipady=10)
        ttk.Button(lfrm31, text='Edit', command=self.editRetrCfg).pack(padx=10, pady=10)

        #----- 3.2 Import configuration

        lfrm32 = ttk.LabelFrame(tab2, text='Import configuration')

        frm321 = ttk.Frame(lfrm32)
        self.showImprtCfgFileName = ttk.Entry(frm321, textvariable=self.importConfigFile)
        self.showImprtCfgFileName.pack(side=LEFT, expand=Y, fill=X, padx=2, pady=6)
        ttk.Button(frm321, text='...', command=self.setImprtCfgFileName, width=2)\
            .pack(side=RIGHT, padx=2, pady=6, expand=N)

        frm322 = ttk.Frame(lfrm32)
        self.txtImprtCfg = Text(frm322, wrap=WORD, width=40, height=10)
        vscroll2 = ttk.Scrollbar(frm322, orient=VERTICAL, command=self.txtImprtCfg.yview)
        self.txtImprtCfg['yscroll'] = vscroll2.set
        vscroll2.pack(side=RIGHT, fill=Y)
        self.txtImprtCfg.pack(fill=BOTH, expand=Y, padx=2, pady=2)

        self.txtImprtCfg.insert(END, self.importConfigFileContent)

        frm321.pack(side=TOP, expand=N, fill=X, padx=6, pady=6)
        frm322.pack(side=TOP, expand=Y, fill=BOTH, ipadx=10, ipady=10)
        ttk.Button(lfrm32, text='Edit', command=self.editImprtCfg).pack(padx=10, pady=10)

        #----- Wrap up

        lfrm31.pack(side=LEFT, expand=Y, fill=BOTH, padx=6, pady=6)
        lfrm32.pack(side=LEFT, expand=Y, fill=BOTH, padx=6, pady=6)

        #=== Finally, a status bar

        status = StatusBar(parent)
        status.pack(side=BOTTOM, fill=X)
        status.set("Loaded.")

    def help(self):
        '''
        Show a short help information
        '''
        win = Toplevel(self.parent)
        win.title("Help")
        hlp = '''
        ARES Data Retrieval and Import Tool

        This tool is a front end to the corresponding import and retrieval Python scripts,
        developed to import data in CSV (or XML in the future) format into the ARES Hadoop
        cluster, or retrieve data from it in and save them in the form of FITS files.

        A set of parameters is needed for each operation, as well as a user-defined
        configuration file.  This is further explained below.


        Import data files to ARES

        For importing existing data, in the form of existing CSV files, the following
        information is needed:

        - Directory where the data files are stored or
        - Wildcard template file name
        - Description file (for non-existing parameters mainly)
        - ARES Runtime folder.
        - Import subdirectory where ARES should look for the files to be imported
        - Type of the data in the files (in case it cannot be deduced by the system)

        If ARES Runtime folder is not specified, then ~/ARES_RUNTIME is assumed,
        unless the environment variable ARES_RUNTIME is set.

        Note that when specifying a definition file, the "paramdef|parameter" part of
        the import folder must be omitted.


        Data retrieval

        For the retrieval of parameter data frmo the ARES cluster, in the form of
        FITS files (with Binary Table Extensions), the following information is required:

        - Parameter IDs (initial and final)
        - Alternatively, a set of parameter IDs or names can be used (TBD)
        - Size of ID block (for the split of the FITS files)
        - Start and End data of the data block to be retrieved.

        Note that the start and the end date can be specified in Year-Month-Day or
        Year-Day_of_Year forms.

        With this information, the system retrieves the data requested and stores them
        in Binary Table Extensions in FITS files.  The size of ID block specifies the
        maximum number of parameters stored in a single FITS file.
'''
        hlp = re.sub('\n +', '\n', hlp) # remove leading whitespace from each line
        t = CustomText(win, wrap='word', width=65, height=40, borderwidth=20, relief=FLAT)
        t.pack(sid='top',fill='both',expand=True)
        t.tag_configure('title', font=('Times', 16, 'bold'), justify=CENTER)
        t.tag_configure('subtitle', font=('Times', 12, 'bold italic'))
        t.tag_configure('centered', justify=CENTER)
        t.tag_configure('emph', font=('Times', 9, 'bold italic'))
        t.tag_configure('blue', foreground='blue')
        t.tag_configure('red', background='red')
        t.insert('1.0', hlp)
        t.apply_tag(tag='title', pattern='^ARES Data Retrieval and Import Tool')
        t.apply_tag(tag='subtitle', pattern='^Import data files to ARES')
        t.apply_tag(tag='subtitle', pattern='^Data retrieval')
        t.apply_tag(tag='blue', pattern='ARES_RUNTIME', )
        t.apply_tag(tag='emph', pattern='(Year-Month-Day|Year-Day_of_Year|CSV|XML| ARES |FITS)')
        t.apply_tag(tag='blue', pattern='^- .*')
        ttk.Button(win, text='OK', command=win.destroy).pack()

    def about(self):
        '''
        Show simple About... dialog
        '''
        win = Toplevel(self.parent)
        win.title("About")
        t = CustomText(win, wrap='word', width=60, height=9, borderwidth=0)
        t.insert('1.0', 'XAresTools\n', ('title'))
        t.insert(END, 'The AresTools interface\n\n', ('subtitle'))
        t.insert(END, 'This application is a simplified interface to the\n')
        t.insert(END, 'AresTools scripts, to make their use a bit easier.\n\n')
        t.insert(END, 'The Euclid SOC Team at ESAC\n')
        t.pack(sid='top',fill='both',expand=True)
        t.tag_configure('title', font=('Times', 16, 'bold'))
        t.tag_configure('subtitle', font=('Times', 12, 'bold italic'))
        t.tag_configure('centered', justify=CENTER)
        t.apply_tag(tag='centered', pattern='^.')
        ttk.Button(win, text='OK', command=win.destroy).pack()

    def quit(self):
        '''
        Quit the application
        '''
        self.parent.destroy()

    def readConfig(self):
        '''
        Read application configuration from appropriate .config folder in HOME directory
        '''
        self.home = os.getenv('HOME')
        self.cfgFolder = '{}/.config/aresri'.format(self.home)
        self.cfgFile = os.path.join(self.cfgFolder, 'aresri.json')
        createDirIfNotExist(the_dir=self.cfgFolder)
        if os.path.isfile(self.cfgFile):
            with open(self.cfgFile, 'r') as cfgf:
                self.cfgData = json.load(cfgf)
        else:
            self.cfgData = {
                'db': {
                    'host': '10.66.180.15',
                    'port': 3306,
                    'user': 'ares',
                    'pwd': '$$ares$$',
                    'db': 'ARES_DB'
                },
                'ares_runtime': os.path.join(self.home, 'ARES_RUNTIME'),
                'pyares_config': os.path.join(self.cfgFolder, 'retrieval_config.ini'),
                'import_config': os.path.join(self.cfgFolder, 'import_config.json')
            }
            self.writeConfig()

        RetrievalConfigFile = self.cfgData['pyares_config']
        ImportConfigFile = self.cfgData['import_config']

    def writeConfig(self):
        '''
        Write configuration to appropriate .config folder in HOME directory
        '''
        with open(self.cfgFile, 'w') as cfgf:
            json.dump(self.cfgData, cfgf)

    def menuCallback(self, item):
        '''
        Callback for the menu bar menu options
        '''
        pass

    def selectParamIds(self):
        self.spbxFromPid.enable()
        self.spbxToPid.enable()
        self.spbxPidsBlock.enable()
        self.lstParamNames.config(state=DISABLED)

    def selectParamNames(self):
        self.spbxFromPid.disable()
        self.spbxToPid.disable()
        self.spbxPidsBlock.disable()
        self.lstParamNames.config(state=NORMAL)

    def greetings(self, msg):
        '''
        Says hello
        '''
        logging.info('='*60)
        logging.info(msg)
        logging.info('='*60)

    def retrieveData(self):
        '''
        Callback to retrive data from ARES cluster
        '''
        # Get information
        #print(json.dumps(self.getRetrievalParams()))
        #self.retrOut.delete('1.0', END)
        #self.retrOut.pack(expand=Y, fill=BOTH)
        #for path in run('find . -name "*.so" -ls'):
        #    print(path)
        #    self.retrOut.insert(END, path)
        retrParams = self.getRetrievalParams()

        tm_start = (list(retrParams['from_date_time'][retrParams['from_date_time']['mode']]) +
                    list(retrParams['from_date_time']['time']))
        tm_end = (list(retrParams['to_date_time'][retrParams['to_date_time']['mode']]) +
                  list(retrParams['to_date_time']['time']))
        pid1, pid2, pidblk = (retrParams['from_pid'], retrParams['to_pid'], retrParams['pids_step'])
        rqstm = retrParams['mode']
        rqstnames = retrParams['selected_names']

        if rqstm == 'name' and len(rqstnames) < 1:
            logging.error('No parameters are selected!')
            return
        if rqstm == 'pid' and pid1 > pid2:
            logging.error('<From-PID> must be less or equal to <To-PID>')

        filename_tpl = 'ares_%F-%T_%f-%t_%YMD1T%hms1-%YMD2T%hms2'
        if rqstm == 'name':
            filename_tpl = 'ares_%F_%N_%YMD1T%hms1-%YMD2T%hms2'

        retriever = Retriever(cfg_file=self.cfgData['pyares_config'],
                              rqst_mode=rqstm, names=rqstnames,
                              from_pid=pid1, to_pid=pid2, pids_block=pidblk,
                              from_date=tm_start, to_date=tm_end,
                              output_dir='./', file_tpl=filename_tpl)

        retr_time_total, conv_time_total, full_time_total, param_names_invalid, gen_files = retriever.run()

    def editRetrCfg(self):
        '''
        Edit retrieval data from ARES parameter configuration file
        '''
        launch_modal_editor(parent=self.parent, file=self.retrieveConfigFile.get())

    def setRetrCfgFileName(self):
        '''
        Select retrieval config. file name
        '''
        filepath = filedialog.askopenfilename()
        if filepath != None  and filepath != '':
            self.retrieveConfigFile.set(filepath)
            self.txtRetrCfg.delete('1.0', END)
            self.txtRetrCfg.insert(END, getContentOfFile(file=filepath))

    def getRetrievalParams(self):
        '''
        Get JSON object with the current retrieval configuration parameters
        '''
        return {
            'mode': self.paramRqstMode.get(),
            'selected_names': [self.lstParamNames.get(idx)
                               for idx in self.lstParamNames.curselection()],
            'from_pid': int(self.spbxFromPid.get()),
            'to_pid': int(self.spbxToPid.get()),
            'pids_step': int(self.spbxPidsBlock.get()),
            'from_date_time': self.fromDateTime.get(),
            'to_date_time': self.toDateTime.get()
        }

    def equalFromTo(self):
        '''
        Set TO date equal to FROM date
        '''
        self.toDateTime.set(components = self.fromDateTime.get())
        if self.fromDateTime.mode() == 'ymd':
            self.toDateTime.useYMD()
        else:
            self.toDateTime.useYDoY()

    def importData(self):
        '''
        Callback for data import into ARES cluster database
        '''
        self.greetings('ARES Import & Retrieval Tool - Data Import')
        imprtParams = self.getImportParameters()
        #print(json.dumps(imprtParams))
        importer = Importer(data_dir=imprtParams['input_dir'],
                            input_file=imprtParams['input_files'],
                            desc_file=imprtParams['description_file'],
                            import_dir=imprtParams['import_dir'],
                            ares_runtime=imprtParams['ares_runtime'],
                            data_type=imprtParams['data_type'],
                            cfg_file=self.cfgData['import_config'],
                            batch_mode=True)
        importer.run_import()

    def getImportParameters(self):
        '''
        Get JSON object with the current import configuration parameters
        '''
        useParDescFile = (self.useParamDescripFile.get() == 'yes')
        useCommonParDataType = (self.useSameParamDataType.get() == 'yes')

        return {
            'input_dir': self.inputDir.get(),
            'input_files': self.inputFiles.get(),
            'ares_runtime': self.aresRunTime.get(),
            'description_file': self.descFile.get() if useParDescFile else '',
            'import_dir': self.paramImpFolder.get(),
            'data_type': self.paramDataType.get() if useCommonParDataType else ''
        }

    def useInputDir(self):
        '''
        Activate the selection of an input data folder
        '''
        self.edInputDir.config(state=NORMAL)
        self.edInputFiles.config(state=DISABLED)

    def useInputFiles(self):
        '''
        Activate the selection of a input file (or template)
        '''
        self.edInputDir.config(state=DISABLED)
        self.edInputFiles.config(state=NORMAL)

    def setInputDir(self):
        '''
        Allow the user to select the input directory with the files to be imported
        '''
        dirpath = filedialog.askdirectory()
        if dirpath != None  and dirpath != '':
            self.inputDir.set(dirpath)

    def setInputFiles(self):
        '''
        Allow the user to select an input file
        '''
        filepath = filedialog.askopenfilename()
        if filepath != None  and filepath != '':
            self.inputFiles.set(filepath)

    def setAresRunTime(self):
        '''
        Allow the user to select the ARES Run Time folder
        '''
        dirpath = filedialog.askdirectory()
        if dirpath != None  and dirpath != '':
            self.aresRunTime.set(dirpath)

    def onChangedRunTime(self, sv):
        importFldr = '{}/import'.format(self.cfgData['ares_runtime'])
        self.importFolders = [x[0].replace(importFldr + '/','')
                              for x in os.walk(importFldr)
                              if not re.search('failed', x[0])][1:]
        self.cboxParamDataType['values'] = self.importFolders

    def setDescripFile(self):
        '''
        Requests the user a description file
        '''
        filepath = filedialog.askopenfilename()
        if filepath != None  and filepath != '':
            self.descFile.set(filepath)

    def changedUseParamDescFile(self):
        '''
        Activate description file line edit or disable it
        '''
        activate = (self.useParamDescripFile.get() == 'yes')
        new_state = NORMAL if activate else DISABLED
        self.edDescripFile.config(state=new_state)

    def changedUseSameParamDataType(self):
        '''
        Activate combo box to select common datatype or disable it
        '''
        activate = (self.useSameParamDataType.get() == 'yes')
        new_state = NORMAL if activate else DISABLED
        self.cboxParamDataType.config(state=new_state)

    def editImprtCfg(self):
        '''
        Edit import into ARES parameter configuration file
        '''
        launch_modal_editor(parent=self.parent, file=self.importConfigFile.get())

    def setImprtCfgFileName(self):
        '''
        Select import config. file name
        '''
        filepath = filedialog.askopenfilename()
        if filepath != None  and filepath != '':
            self.importConfigFile.set(filepath)
            self.txtImprtCfg.delete('1.0', END)
            self.txtImprtCfg.insert(END, getContentOfFile(file=filepath))


if __name__ == '__main__':
    print('This is a library class and cannot be executed.')
    sys.exit()
