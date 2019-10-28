#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
controller.py

Module with the Controller class

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

from tools.dirwatcher import define_dir_watcher
from tools.actions import ActionsLauncher

import time

import json
import queue

from copy import deepcopy
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

class Controller:
    """
    Class Controller

    Implements methods to monitor the different folders in the SOC IF
    implementation, and controls the actions to take, according to the
    different action objects.
    """

    # The following object is used as a template for the actions to be
    # executed when a new file appears in the folder where it is
    # placed.
    #
    # The 'type' can be: 'int' (internal), 'cmd', 'bash_script',
    # 'python2' or 'python' (for Pyhton 3)
    #
    # In the 'args' item, the following variables are replaced:
    # - {file_name}: the base file of the new file
    # - {file_path}: the full file name, included the path, of the new file
    # - {src_dir}: the source dir, (the folder where the actions object is located)
    # - {tgt_dir}: the target directory, according to the config. file
    # - {this_dir}: the directory where the actions object file is located
    # - {base_dir}: the SOC IF base dir, according to the configuration
    #
    # The working directory for the execution of the script is the
    # path where the actions object is located.
    #
    # At the initialization, an dummy actions object file is created.
    # Edit it and add blocks to the 'actions' array.

    LoopSleep = 1.0

    def __init__(self, cfg_file, create_folders=True, base_path=None):
        self.queues = []
        self.cfg = self.loadConfiguration(file=cfg_file)
        pprint(self.cfg['base_path'])
        pprint(base_path)
        if base_path:
            self.cfg['base_path'] = base_path
        self.baseDir = self.cfg['base_path']
        self.dirWatchers = []
        self.launcher = ActionsLauncher(self.baseDir)
        self.create_folders = create_folders

    @staticmethod
    def loadConfiguration(file):
        """
        Load configuration file
        :param file: The path of the configuration file name
        :return: -
        """
        try:
            with open(file, 'r') as fcfg:
                cfg = json.load(fcfg)
        except Exception as ee:
            logger.error('Cannot open configuration file {}'.format(file))
            logger.fatal('{}'.format(ee))
            return None

        return cfg

    @staticmethod
    def createIfNotExists(folder):
        """
        Create a nested folder if it does not exist
        :param folder: The folder to create
        """
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info('Creating folder {}'.format(folder))
            return True
        else:
            logger.info('Folder {} already exists'.format(folder))
            return False

    @staticmethod
    def idToPath(base, src, io, data):
        """
        Build the relative (if base is None) or the complete path for a
        data flow folder
        :param base: Base path for the entire folder structure
        :param src: Source identifier
        :param io: in/out
        :param data: Data flow identifier
        :return: The built path as a string
        """
        actualId = src.replace('_', '/')
        relPath = os.path.join(actualId, io)
        if data is not None:
            relPath = os.path.join(relPath, data)
        if base is None:
            return relPath
        else:
            return os.path.join(base, relPath)

    def createActions(self, src, tgts, acts):
        """
        Create the actions object file according to the internal and external provided,
        and save it to file
        :param src: The src subsystem
        :param tgts: The target subsystem(s)
        :param acts: Object with lists of internal and external action objects
        :return: True if succeeded, False otherwise
        """
        # Initialize actions object from the template
        actions = deepcopy(ActionsLauncher.ActionsObjectTpl)
        actions['actions'].clear()

        # Internal archive action (make it first)
        if 'archive' in acts:
            actions['actions'].append(ActionsLauncher.ActionInternalSaveLocalArch)
            acts.remove('archive')

        # Parse rest of actions
        for act in acts:
            if isinstance(act, dict):
                actions['actions'].append(act)
            else:
                newAct = deepcopy(ActionsLauncher.InternalActions[act])
                newAct['type'] = 'int'
                newAct['args'] = ';'.join(tgts)
                actions['actions'].append(newAct)

        # Save actions file
        try:
            with open(os.path.join(src, 'actions.json'), 'w') as fact:
                fact.write(json.dumps(actions, indent=4))
            return True
        except:
            return False

    def initMonitoring(self, folderA, folderB):
        """
        Create a dummy actions object file and launch monitoring
        :param folderA: The FROM folder to create
        :param folderB: The TO folder to create
        :param init_actions: Create initial, dummy action object file
        :param archive: Add archive internal action if True
        """
        # Launch monitoring
        qa = queue.Queue()
        dwThrA = define_dir_watcher(folderA, qa)
        self.queues.append({'from': folderA, 'to': folderB,
                            'this_folder_is': 'from',
                            'queue': qa, 'thread': dwThrA})
        self.dirWatchers.append(dwThrA)

    def initialize(self, cfg : dict, create_folders=False):
        """
        Ensure the folders exist
        :param cfg: The configuration dictionary
        :param create_folders: True, to create IO folders
        :return: -
        """
        logger.info('SIS Controller Base Path: {}'.format(self.baseDir))
        logger.info('Ensuring the SIS folders exist under base path')

        # Get identifiers
        identifiers = dict(cfg['id'])
        ids = (identifiers if create_folders else {})

        # Get predefined actions and substitute env. vars.
        predefined_actions = dict(cfg['predefined_actions'])
        for id,act in predefined_actions.items():
            act['id'] = id
            for k,v in act.items():
                if len(v) < 1:
                    continue
                if v[0] == '$':
                    act[k] = os.getenv(v[1:], 'UNKNOWN')
        ActionsLauncher.InternalActions.update(predefined_actions)
        #pprint(ActionsLauncher.InternalActions)

        # Create main folders, and read-me files
        for elem, acronym in ids.items():
            for ep in ['in', 'out']:
                endPoint = self.idToPath(self.baseDir, acronym, ep, None)
                self.createIfNotExists(endPoint)
            readmeFileName = self.idToPath(self.baseDir, acronym, 'README.md', None)
            with open(readmeFileName, "w") as fp:
                fp.write(("{} Exchange Folder\n" +
                          "============================\n\n" +
                          "This Folder contains the input (`in`) and output \n" +
                          "(`out`) folders (from the perspective of the SIS \n" +
                          "subsystem) to exchange data flows between external \n" +
                          "systems and SOC subsystems.\n" +
                          "This data flow circulation is handled by the SIS \n" +
                          "subsystem.\n\n" +
                          "The actions triggered by the appearance of an data \n" +
                          "file in the `in` folders are defined in the \n" +
                          "appropriate `actions.json` files.\n\n").format(elem))

        # Create folders for flow transfer, according to configuration file
        for dflow in list(cfg['data_flows']):
            flowName = dflow['group']
            logger.info('Setting up folders for flow {}'.format(flowName))
            for dataId, dataSpec in dflow['flows'].items():
                datasetName = dataSpec['name']
                logger.info('- Data set {}'.format(datasetName))

                from_elem = dataSpec['source']
                circSourceDir = self.idToPath(self.baseDir, identifiers[from_elem], 'in', dataId)
                if create_folders: self.createIfNotExists(circSourceDir)

                circTargetDirs = []
                toEndPoints = []
                for to_elem, acts in dataSpec['target'].items():
                    idToElem = identifiers[to_elem]
                    relTargetDir = self.idToPath(None, idToElem, 'out', dataId)
                    circTargetDir = self.idToPath(self.baseDir, idToElem, 'out', dataId)
                    if create_folders: self.createIfNotExists(circTargetDir)

                    circTargetDirs.append(circTargetDir)
                    toEndPoints.append(relTargetDir)

                    # Create actions for target subsystem
                    if not self.createActions(circTargetDir, [], acts):
                        logger.error('Could not create target folder actions for {} => {}'.\
                                     format(from_elem, to_elem))

                    # Initialize and launch monitoring for the each target folder
                    self.initMonitoring(circTargetDir, [])

                # Create actions for source subsystem
                if not  self.createActions(circSourceDir, toEndPoints, dataSpec['actions']):
                    logger.error('Could not create source folder actions for ' +
                                 '{} => {}'.format(from_elem, ','.join(dataSpec['target'].keys())))

                # Initialize and launch monitoring for the source folder
                self.initMonitoring(circSourceDir, toEndPoints)

                logger.debug('>>> {}::{} : {} => {}'.format(flowName, datasetName,
                                                            #fromEndPoint,
                                                            from_elem,
                                                            ';'.join(toEndPoints)))

        # Create additional, management folders
        if create_folders:
            for d in ['local_archive']:
                self.createIfNotExists(os.path.join(self.baseDir, d))

    def monitor(self):
        """
        Check all the queues, looking for new entries, and launching the
        appropriate action (according to the actions object file
        :return: -
        """
        for item in self.queues:
            fromFolder = item['from']
            toFolder = item['to']
            thisFolder = item[item['this_folder_is']]
            q : queue.Queue = item['queue']
            while not q.empty():
                entry = q.get()
                bentry = os.path.basename(entry)
                if entry[-5:] == '.part' or \
                    bentry == 'actions.json' or \
                    bentry[0:4] == 'log.' or \
                    bentry[0:4] == 'err.':
                    continue
                logger.info('New file {}'.format(entry))

                logger.info('Launching...')
                self.launcher.launchActions(folder=thisFolder, file=entry,
                                            src_dir=fromFolder, tgt_dir=toFolder)
                logger.info('done.')

    def run(self):
        """
        Launch the Controller process
        :return: -
        """

        # Create / List folders
        self.initialize(cfg=self.cfg, create_folders=self.create_folders)

        # Run main loop
        self.runMainLoop()

        # When main loop is finished, wrap up and end program
        self.terminate()

    def runMainLoop(self):
        """
        Run loop of Master
        :return: -
        """
        logger.info('START')
        iteration = 0

        try:
            while True:
                iteration = iteration + 1
                logger.debug('Iteration {}'.format(iteration))

                # Perform check of queues
                self.monitor()

                time.sleep(Controller.LoopSleep)

        except Exception as ee:
            logger.error('{}'.format(ee))
            logger.debug('Iteration {}'.format(iteration))


    def terminate(self):
        """
        Wrap-up and finish execution
        :return: -
        """
        logger.info('END')
        for thr in self.dirWatchers:
            thr.join()


def main():
    pass


if __name__ == '__main__':
    main()
