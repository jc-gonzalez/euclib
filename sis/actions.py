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

from pprint import pprint

import pytest

from .filetx import Tx

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

    ActionInternalMove = {'id': 'move',
                          'type': 'int',
                          'command': 'move',
                          'args': ''}

    ActionInternalSaveLocalArch = {'id': 'archive',
                                   'type': 'int',
                                   'command': 'archive',
                                   'args': ''}

    ActionInternalRemoteCopy = {'id': 'remote_copy',
                                'type': 'int',
                                'command': 'remote_copy',
                                'host': '',
                                'user': '',
                                'pwd': '',
                                'tgt_dir': '',
                                'args': ''}

    ActionInternalRemoteMove = ActionInternalRemoteCopy.update({'id': 'remote_move'})

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

    def runia_archive(self, from_file):
        """
        Run Internal Action: Archive file
        :param from_file: The file to archive
        :return: -
        """
        arcDir = os.path.join(self.basePath, 'local_archive')
        logger.debug('{} => {}'.format(from_file, arcDir))
        tx = Tx()
        tx.file(from_file).toDir(arcDir).link()

    def runia_move(self, from_file, to_folder):
        """
        Run Internal Action: Move file to another folder
        :param from_file: The file to move
        :param to_folder: The directory where to move the file
        :return: -
        """
        if isinstance(to_folder, list):
            fld = to_folder[0]
        else:
            fld = to_folder
        if not fld: return
        tgtDir = fld if fld[0] == '/' \
                 else os.path.join(self.basePath, fld)
        logger.debug('Distribute: {} => {}'.format(from_file, tgtDir))
        tx = Tx()
        tx.file(from_file).toDir(tgtDir).move()

    def runia_distribute(self, from_file, to_folders):
        """
        Run Internal Action: Distribute file to multiple folders
        :param from_file: The file to distribute
        :param to_folders: List of directories where to distribute the file
        :return: -
        """
        if not to_folders[0]: return
        tgtDirs = to_folders if to_folders[0][0] == '/' \
                  else [os.path.join(self.basePath, x) for x in to_folders]
        logger.debug('Distribute: {} => {}'.format(from_file, ','.join(tgtDirs)))
        tx = Tx()
        tx.file(from_file).toDir(tgtDirs[0]).move_and_set()
        for tgtDir in tgtDirs[1:]:
            tx.toDir(tgtDir).link()

    def runia_remote_copy(self, from_file, host, user, pwd, folder, is_move=False):
        """
        Run Internal Action: Copy/Move file to a folder in another host
        :param from_file: The file to move
        :param host: The remote host
        :param user: The remote user
        :param pwd: The password for that user
        :param folder: The directory where to put the file in the host
        :param is_move: True, to move the file (instead of copy)
        :return: -
        """
        logger.debug('RemoteCopy: {} =>{}:{}@{}:{} ({})'\
                     .format(from_file, user, pwd, host, folder,
                             ('MOVE' if is_move else 'COPY')))
        tx = Tx()
        txx = tx.file(from_file).host(host).user(user).pwd(pwd).toDir(folder)
        if is_move:
            txx.remote_move()
        else:
            txx.remote_copy()

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
        logger.debug(json.dumps(act_vars))
        if args: act_vars['tgt_dir'] = dirs
        from_file = act_vars['file_path']

        try:
            if action == 'archive':
                self.runia_archive(from_file=from_file)
            elif action == 'move':
                self.runia_move(from_file=from_file,
                                to_folder=act_vars['tgt_dir'])
            elif action == 'distribute':
                self.runia_distribute(from_file=from_file,
                                      to_folders=act_vars['tgt_dir'])
            elif action in ('remote_copy', 'remote_move'):
                self.runia_remote_copy(from_file=from_file,
                                       host=act_vars['host'],
                                       user=act_vars['user'],
                                       pwd=act_vars['pwd'],
                                       folder=act_vars['tgt_dir'],
                                       is_move=(action=='remote_move'))
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

## TESTS

import random, string

def rndStr(n=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def tmpDirName(n=8):
    return os.path.join(os.getenv('HOME'), '.test', rndStr(n))

class TestActionsLauncher:

    @pytest.fixture
    def base_path(self):
        baseDir = tmpDirName()
        os.makedirs(baseDir)
        os.makedirs(os.path.join(baseDir, 'local_archive'))
        yield baseDir
        shutil.rmtree(baseDir)

    @pytest.fixture
    def internal_action_distribute_folder(self):
        tmpDir = tmpDirName()
        os.makedirs(tmpDir)
        acts = {
            'last_update': '',
            'history': ['Test actions file'],
            'actions': [ActionsLauncher.ActionInternalDistribute]
        }
        # Configure internal distribute action
        acts['actions'][0]['args'] = '{0}/dist1;{0}/dist2'.format(tmpDir)

        tmpFile = os.path.join(tmpDir, 'actions.json')
        with open(tmpFile, 'w') as fa:
            json.dump(acts, fa, indent=4)

        yield tmpDir
        shutil.rmtree(tmpDir)

    @pytest.fixture
    def internal_action_move_folder(self):
        tmpDir = tmpDirName()
        os.makedirs(tmpDir)
        acts = {
            'last_update': '',
            'history': ['Test actions file'],
            'actions': [ActionsLauncher.ActionInternalMove]
        }
        # Configure internal move action
        acts['actions'][0]['args'] = "{0}/mv;".format(tmpDir)

        tmpFile = os.path.join(tmpDir, 'actions.json')
        with open(tmpFile, 'w') as fa:
            json.dump(acts, fa, indent=4)

        yield tmpDir
        shutil.rmtree(tmpDir)

    @pytest.fixture
    def internal_action_archive_folder(self):
        tmpDir = tmpDirName()
        os.makedirs(tmpDir)
        acts = {
            'last_update': '',
            'history': ['Test actions file'],
            'actions': [ActionsLauncher.ActionInternalSaveLocalArch]
        }

        tmpFile = os.path.join(tmpDir, 'actions.json')
        with open(tmpFile, 'w') as fa:
            json.dump(acts, fa, indent=4)

        yield tmpDir
        shutil.rmtree(tmpDir)

    @pytest.fixture
    def internal_action_remote_folder(self):
        tmpDir = tmpDirName()
        os.makedirs(tmpDir)
        acts = {
            'last_update': '',
            'history': ['Test actions file'],
            'actions': [ActionsLauncher.ActionInternalRemoteCopy,
                        ActionsLauncher.ActionInternalRemoteMove]
        }
        # Configure internal remote copy action
        credentials = {'host': 'eucdev.n1data.lan',
                                'user': 'eucops',
                                'pwd': 'eu314clid',
                                'tgt_dir': '/tmp'}
        acts['actions'][0].update(credentials)
        credentials['tgt_dir'] = '/home/eucops'
        acts['actions'][1].update(credentials)

        tmpFile = os.path.join(tmpDir, 'actions.json')
        with open(tmpFile, 'w') as fa:
            json.dump(acts, fa, indent=4)

        yield tmpDir
        shutil.rmtree(tmpDir)

    def create_dirs_and_file(self, tmpDir, dirs, fileno):
        for d,subd in dirs.items():
            for sd in subd:
                fld = os.path.join(d, sd)
                os.mkdir(fld)
                logger.info('Folder {} created'.format(fld))

        datFile = os.path.join(tmpDir, 'example{}.dat'.format(fileno))
        with open(datFile, 'w') as fe:
            fe.write('{"title": "Example file"}')

        return datFile

    def test_launch_internal_distribute_action(self, base_path, internal_action_distribute_folder):
        baseDir = base_path
        tmpDir = internal_action_distribute_folder
        datFile = self.create_dirs_and_file(tmpDir, {tmpDir: ['dist1', 'dist2']}, 1)

        actLnch = ActionsLauncher(basePath=baseDir)
        actLnch.launchActions(folder=tmpDir, file=datFile, src_dir=tmpDir, tgt_dir=[''])

        assert not os.path.exists(os.path.join(tmpDir, 'example1.dat'))
        assert os.path.exists(os.path.join(tmpDir, 'dist1', 'example1.dat'))
        assert os.path.exists(os.path.join(tmpDir, 'dist2', 'example1.dat'))

    def test_launch_internal_move_action(self, base_path, internal_action_move_folder):
        baseDir = base_path
        tmpDir = internal_action_move_folder
        datFile = self.create_dirs_and_file(tmpDir, {tmpDir: ['mv']}, 2)

        actLnch = ActionsLauncher(basePath=baseDir)
        actLnch.launchActions(folder=tmpDir, file=datFile, src_dir=tmpDir, tgt_dir=[''])

        assert not os.path.exists(os.path.join(tmpDir, 'example2.dat'))
        assert os.path.exists(os.path.join(tmpDir, 'mv', 'example2.dat'))

    def test_launch_internal_archive_action(self, base_path, internal_action_archive_folder):
        baseDir = base_path
        tmpDir = internal_action_archive_folder
        datFile = self.create_dirs_and_file(tmpDir, {tmpDir: []}, 3)

        actLnch = ActionsLauncher(basePath=baseDir)
        actLnch.launchActions(folder=tmpDir, file=datFile, src_dir=tmpDir, tgt_dir=[''])

        assert os.path.exists(os.path.join(tmpDir, 'example3.dat'))
        assert os.path.exists(os.path.join(baseDir, 'local_archive', 'example3.dat'))


def main():
    pass


if __name__ == '__main__':
    main()
