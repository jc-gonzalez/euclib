#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
'''

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

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
import os, sys
import re
import time
import datetime
import logging
import argparse

import subprocess
import configparser
import json

# details
__author__ = "J C Gonzalez"
__copyright__ = "Copyright 2015-2019, J C Gonzalez"
__license__ = "LGPL 3.0"
__version__ = "0.1"
__maintainer__ = "J C Gonzalez"
__email__ = "jcgonzalez@sciops.esa.int"
__status__ = "Development"
#__url__ = ""


class EntrySpinbox(ttk.Frame):
    def __init__(self, master, label='Enter data:', first=1, last=100):
        self.data = StringVar()

        ttk.Frame.__init__(self, master)
        ttk.Label(self, text=label).pack(side=LEFT, padx=2, pady=2)
        self.spbx = Spinbox(self, textvariable=self.data, from_=first, to=last)
        self.spbx.pack(side=LEFT, expand=1, fill=X, padx=2, pady=2)

    def get(self):
        return self.data.get()

    def set(self, value):
        self.data.set(value)

    def enable(self):
        return self.spbx.config(state=NORMAL)

    def disable(self):
        return self.spbx.config(state=DISABLED)


class YMDSpinboxes(ttk.Frame):
    '''
    Handy class to add three spinboxes to set the date as year-month-day
    '''
    def __init__(self, master):
        self.year = StringVar()
        self.month = StringVar()
        self.day = StringVar()

        ttk.Frame.__init__(self, master)
        self.spbxYear = Spinbox(self, from_=2010, to=2100, textvariable=self.year, width=6)
        self.spbxYear.grid(row=0, column=0)
        self.dash1 = ttk.Label(self, text=' - ').grid(row=0, column=1)
        self.spbxMonth = Spinbox(self, from_=1, to=12, textvariable=self.month, width=4)
        self.spbxMonth.grid(row=0, column=2)
        self.dash2 = ttk.Label(self, text=' - ').grid(row=0, column=3)
        self.spbxDay = Spinbox(self, from_=1, to=31, textvariable=self.day, width=4)
        self.spbxDay.grid(row=0, column=4)

        self.clear()

    def enable(self):
        self.spbxYear.config(state=NORMAL)
        self.spbxMonth.config(state=NORMAL)
        self.spbxDay.config(state=NORMAL)

    def disable(self):
        self.spbxYear.config(state=DISABLED)
        self.spbxMonth.config(state=DISABLED)
        self.spbxDay.config(state=DISABLED)

    def set(self, year, month, day):
        self.year.set(year)
        self.month.set(month)
        self.day.set(day)

    def get(self):
        return [ int(self.year.get()), int(self.month.get()), int(self.day.get()) ]

    def clear(self):
        self.set(2018, 5, 11)


class YDoYSpinboxes(ttk.Frame):
    '''
    Handy class to add three spinboxes to set the date as year-month-day
    '''
    def __init__(self, master):
        self.year = StringVar()
        self.doy = StringVar()

        ttk.Frame.__init__(self, master)
        self.spbxYear = Spinbox(self, from_=2010, to=2100, textvariable=self.year, width=6)
        self.spbxYear.grid(row=0, column=0)
        self.dash1 = ttk.Label(self, text=' - ').grid(row=0, column=1)
        self.spbxDoy = Spinbox(self, from_=1, to=366, textvariable=self.doy, width=5)
        self.spbxDoy.grid(row=0, column=2)

        self.clear()

    def enable(self):
        self.spbxYear.config(state=NORMAL)
        self.spbxDoy.config(state=NORMAL)

    def disable(self):
        self.spbxYear.config(state=DISABLED)
        self.spbxDoy.config(state=DISABLED)

    def set(self, year, doy):
        self.year.set(year)
        self.doy.set(doy)

    def get(self):
        return [ int(self.year.get()), int(self.doy.get()) ]

    def clear(self):
        self.set(2018, 131)


class HMSmsSpinboxes(ttk.Frame):
    '''
    Handy class to add three spinboxes to set the date as year-month-day
    '''
    def __init__(self, master):
        self.hour = StringVar()
        self.min = StringVar()
        self.sec = StringVar()
        self.msec = StringVar()

        ttk.Frame.__init__(self, master)
        self.spbxHour = Spinbox(self, from_=0, to=23, textvariable=self.hour, width=4)
        self.spbxHour.grid(row=0, column=0)
        self.dash1 = ttk.Label(self, text=' : ').grid(row=0, column=1)
        self.spbxMin = Spinbox(self, from_=0, to=59, textvariable=self.min, width=4)
        self.spbxMin.grid(row=0, column=2)
        self.dash2 = ttk.Label(self, text=' : ').grid(row=0, column=3)
        self.spbxSec = Spinbox(self, from_=0, to=60, textvariable=self.sec, width=4)
        self.spbxSec.grid(row=0, column=4)
        self.dash3 = ttk.Label(self, text='.').grid(row=0, column=5)
        self.spbxMsec = Spinbox(self, from_=0, to=999, textvariable=self.msec, width=5)
        self.spbxMsec.grid(row=0, column=6)

        self.clear()

    def set(self, hour, min, sec, msec):
        self.hour.set(hour)
        self.min.set(min)
        self.sec.set(sec)
        self.msec.set(msec)

    def get(self):
        return [ int(self.hour.get()), int(self.min.get()),
                 int(self.sec.get()), int(self.msec.get()) ]

    def clear(self):
        self.set(0, 0, 0, 0)


class DateTime(ttk.Frame):
    '''
    Handy class to add a simple status bar
    '''
    def __init__(self, master):
        ttk.Frame.__init__(self, master)

        self.dateMode = StringVar(self)
        self.frmDate = ttk.Frame(self)
        rbtn0 = ttk.Radiobutton(self.frmDate, text='Y-M-D', command=self.useYMD,
                                variable=self.dateMode, value='ymd')
        rbtn0.grid(row=0, column=0, padx=20)
        rbtn1 = ttk.Radiobutton(self.frmDate, text='Y-DoY', command=self.useYDoY,
                                variable=self.dateMode, value='ydoy')
        rbtn1.grid(row=1, column=0, padx=20)

        self.ymd = YMDSpinboxes(self.frmDate)
        self.ymd.grid(row=0, column=1)
        self.ydoy = YDoYSpinboxes(self.frmDate)
        self.ydoy.grid(row=1, column=1)

        self.time = HMSmsSpinboxes(self)

        self.frmDate.grid(row=0, column=0)
        self.time.grid(row=0, column=2, padx=10)

        self.dateMode.set('ymd')
        self.useYMD()

    def useYMD(self):
        self.ymd.enable()
        self.ydoy.disable()

    def useYDoY(self):
        self.ymd.disable()
        self.ydoy.enable()

    def set(self, ydoy=False, year=None, month=None, day=None, doy=None,
            hour=None, min=None, sec=None, msec=None, components=None):
        if components:
            year, month, day = components['ymd']
            yeardoy, doy = components['ydoy']
            hour, min, sec, msec = components['time']
            ydoy = components['mode'] == 'ydoy'
            if ydoy:
                year = yeardoy

        if ydoy:
            self.dateMode.set('ydoy')
            self.ydoy.set(year, doy)
        else:
            self.dateMode.set('ymd')
            self.ymd.set(year, month, day)
        self.time.set(hour, min, sec, msec)

    def get(self):
        return { 'mode': self.dateMode.get(),
                 'ymd': self.ymd.get(),
                 'ydoy': self.ydoy.get(),
                 'time': self.time.get() }

    def clear(self):
        self.ydoy.clear()
        self.ymd.clear()
        self.time.clear()

    def mode(self):
        return self.dateMode.get()


class StatusBar(ttk.Frame):
    '''
    Handy class to add a simple status bar
    '''
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.label = ttk.Label(self, relief=SUNKEN, anchor=W)
        self.label.pack(fill=X)

    def set(self, format, *args):
        self.label.config(text=format % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


class CustomText(Text):
    '''A text widget with a new method, HighlightPattern

    example:

    text = CustomText()
    text.tag_configure("red",foreground="#ff0000")
    text.highlightPattern("this should be red", "red")

    The HighlightPattern method is a simplified python
    version of the tcl code at http://wiki.tcl.tk/3246
    '''
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)

    def apply_tag(self, pattern=None, tag=None, regexp=True):
        '''
        Apply the given tag to all text that matches the given pattern
        '''

        #self.mark_set('matchStart', '1.0')
        start = '1.0'

        count = IntVar()
        while True:
            index = self.search(pattern, start, END, count=count, regexp=regexp)
            if index == '': break
            endSrch = '{}+{}c'.format(index, count.get())
            #print('match: {} - {}'.format(index, endSrch))
            self.tag_add(tag, index, endSrch)
            start = endSrch
            #print('added tag {}'.format(tag))

if __name__ == '__main__':
    print('This is a library class and cannot be executed.')
    sys.exit()
