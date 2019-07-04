#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
actions.py

Module for defining internal, and parse and execute external actions
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

import json
import re
import subprocess
import shutil
import traceback

#from pprint import pprint

from enum import Enum

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

class TxMode(Enum):
    """
    Mode to transfer files
    """
    MOVE      = 'move'
    MOVE_ORIG = 'move_orig'
    LINK      = 'link'
    COPY      = 'copy'

class Tx:
    """
    Class to perform a transfer of a file
    """
    def __init__(self):
        """
        Initialization of Tx class
        """
        self.file_full = None
        self.to_dir = None

    def file(self, pth):
        """
        Set file to transfer
        :param pth: Full file path
        :return: -
        """
        self.file_full = pth
        return self

    def toDir(self, pth):
        """
        Set target directory
        :param pth: File path
        :return: -
        """
        self.to_dir = pth
        return self

    def move(self):
        """
        Move the file
        :return: -
        """
        return self.go(mode=TxMode.MOVE)

    def move_and_set(self):
        """
        Move the file, and set as the new source
        :return: -
        """
        return self.go(mode=TxMode.MOVE_ORIG)

    def copy(self):
        """
        Copy the file
        :return: -
        """
        return self.go(mode=TxMode.COPY)

    def link(self):
        """
        Link the file
        :return: -
        """
        return self.go(mode=TxMode.LINK)

    def go(self, mode=TxMode.MOVE):
        """
        Make the relocation
        :param mode: The way to perform the relocation
        :return:
        """
        if mode == TxMode.COPY:
            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            shutil.copy(self.file_full, new_file + '.part')
            shutil.move(new_file + '.part', new_file)
        elif mode == TxMode.MOVE or mode == TxMode.MOVE_ORIG:
            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            shutil.move(self.file_full, new_file + '.part')
            shutil.move(new_file + '.part', new_file)
            if mode == TxMode.MOVE_ORIG:
                self.file_full = new_file
        elif mode == TxMode.LINK:
            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            os.link(self.file_full, new_file)
        else:
            logger.error('Transfer mode not known!')

        return self


# The following object is used as a template for the actions to be executed when a new file
# appears in the folder where it is placed.
# The 'type' can be:  'int' (internal), 'cmd', 'bash_script', 'python2' or
# 'python' (for Pyhton 3)
# In the 'args' item, the following variables are replaced:
# - {file_name}: the base file of the new file
# - {file_path}: the full file name, included the path, of the new file
# - {src_dir}: the source directory (the folder where the actions object is located
# - {tgt_dir}: the target directory, according to the config. file
# - {this_dir}: the directory where the actions object file is located
# - {base_dir}: the SOC IF base dir, according to the configuration
# The working directory for the execution of the script is the path where the actions object
# is located.
# At the initialization, an dummy actions object file is created.  Edit it and add blocks to
# the 'actions' array.

class ActionsLauncher:
    """
    Class ActionsLauncher

    Implements the methods for the execution of the different actions.
    """
    ActionsObjectTpl = {
        'last_update': '',
        'history': ['Initial creation'],
        'actions': [
            {'id': 'dummy_action_as_template',
             'type': 'cmd',
             'command': '/bin/ls',
             'args': '-l {file_name}'},
        ]
    }

    ActionMoveOn = {'id': 'move_on',
                    'type': 'cmd',
                    'command': 'mv',
                    'args': '{file_path} {tgt_dir}/'}

    ActionInternalDistribute = {'id': 'distribute',
                                'type': 'int',
                                'command': 'distribute',
                                'args': ''}

    ActionInternalSaveLocalArch = {'id': 'archive',
                                   'type': 'int',
                                   'command': 'archive',
                                   'args': ''}

    def __init__(self, basePath):
        self.basePath = basePath

    @staticmethod
    def runCommand(act='action', cmd='/bin/ls', workdir='./', shell=False):
        """
        Run command
        :param act: Action name
        :param cmd: The actual command
        :param workdir: The working directory to execute the command
        :param shell: True to activate shell in subprocess
        :return: True on successful execution, False otherwise
        """
        try:
            logFile = os.path.join(workdir, 'log.{}'.format(act))
            errFile = os.path.join(workdir, 'err.{}'.format(act))
            if not shell:
                cmd = cmd.split(' ')
            logger.debug('Running: {} (shell={})'.format(cmd, shell))
            with open(logFile, 'a') as flog:
                p = subprocess.run(cmd, cwd=workdir,
                                   stdout=flog, stderr=subprocess.PIPE, shell=shell)
            if p.stderr:
                with open(errFile, 'a') as ferr:
                    ferr.write(p.stderr.decode("utf-8"))

            return True
        except Exception as ee:
            #logger.error('{}'.format(ee))
            logger.exception('{}'.format(ee))
            logger.error('Running in ')
            return False

    def runInternalAction(self, action='action', args='', act_vars=None):
        """
        Run an internal action
        :param action: the action name
        :param args: the list of target folders
        :param act_vars: set of variables that apply to this action
        :return: True on successful execution
        """
        if act_vars is None: act_vars = {}
        dirs = [os.path.join(self.basePath, x) for x in args.split(';')]
        logger.debug('Running internal action: {} {}'.format(action, dirs))

        from_file = act_vars['file_path']
        tx = Tx()
        #pprint(env)
        #pprint(args)

        try:
            if action == 'archive':
                arcDir = os.path.join(self.basePath, 'local_archive')
                logger.debug('{} => {}'.format(from_file, arcDir))
                tx.file(from_file).toDir(arcDir).link()
            elif action == 'distribute':
                tgtDirs = [os.path.join(self.basePath,x) for x in act_vars['tgt_dir']]
                tx.file(from_file).toDir(tgtDirs[0]).move_and_set()
                for tgtDir in tgtDirs[1:]:
                    tx.toDir(tgtDir).link()
        except:
            traceback.print_exc(file=sys.stdout)

    def launchActions(self, folder, file, src_dir, tgt_dir):
        """
        Launch the actions specified in the actions.json file whenever a new file appears.
        Note that the following applies to the actions.json file:
        The 'type' can be:  'cmd', 'bash_script', 'python2' or 'python' (for Pyhton 3)
        In the 'args' item, the following variables are replaced:
        - {file_name}: the base file of the new file
        - {file_path}: the full file name, included the path, of the new file
        - {src_dir}: the source directory (the folder where the actions object is located
        - {tgt_dir}: the target directory, according to the config. file
        - {this_dir}: the directory where the actions object file is located
        - {base_dir}: the SOC IF base dir, according to the configuration
        The working directory for the execution of the script is the path where the actions object
        is located.
        :param folder: the folder being monitored
        :param file: the current file being handled
        :param src_dir: source directory
        :param tgt_dir: target directory
        :return: -
        """
        logger.debug('Launching actions in {} on {} ({} =>{})'.format(folder, file,
                                                                      src_dir, tgt_dir))

        try:
            actFile = os.path.join(folder, 'actions.json')
            with open(actFile) as fact:
                act = json.load(fact)
        except Exception as ee:
            logger.error('{}'.format(ee))
            return

        for a in act['actions']:
            actId = a['id']
            actType = a['type']
            actCmd = a['command']
            logger.debug('Executing action >>> {} <<<'.format(actId))

            rep = {"{file_name}": os.path.basename(file),
                   "{file_path}": file,
                   "{src_dir}": src_dir,
                   "{tgt_dir}": tgt_dir,
                   "{base_dir}": self.basePath,
                   "{this_dir}": folder}

            rep = dict((re.escape(k), v) for k, v in rep.items())
            pattern = re.compile("|".join(rep.keys()))
            args = pattern.sub(lambda m: rep[re.escape(m.group(0))], a['args'])

            if actType == 'int':
                logger.debug('Launching internal action "{}" . . .'.format(actCmd))
                env = { x[2:-2]: y for x,y in rep.items() }
                self.runInternalAction(action=actCmd, args=args, act_vars=env)
            else:
                cmd = '{} {}'.format(actCmd, args)

                if actType == 'cmd':
                    logger.debug('Launching Bash command "{}" . . .'.format(cmd))
                    fullCmd = cmd
                elif actType == 'bash_script':
                    logger.debug('Launching Bash script "/bin/bash {}" . . .'.format(cmd))
                    fullCmd = '/bin/bash ' + cmd
                elif actType == 'python2':
                    logger.debug('Launching Python2 script "python2 {}" . . .'.format(cmd))
                    fullCmd = '/usr/local/bin/python2 ' + cmd
                elif actType == 'python':
                    logger.debug('Launching Python3 script "python3 {}" . . .'.format(cmd))
                    fullCmd = '/usr/local/bin/python3 ' + cmd
                else:
                    logger.warning('Unknown action type "{}" '.format(actFile))
                    return

                self.runCommand(act=actId, cmd=fullCmd, workdir=folder, shell=(actType == 'cmd'))


def main():
    pass


if __name__ == '__main__':
    main()
