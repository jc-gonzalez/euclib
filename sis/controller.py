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
from .actions import ActionsLauncher

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

    def __init__(self, cfg_file, create_folders=True):
        self.queues = []
        self.cfg = self.loadConfiguration(file=cfg_file)
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

    def initMonitoring(self, folderA, folderB, init_actions=True, archive=False):
        """
        Create a dummy actions object file and launch monitoring
        :param folderA: The FROM folder to create
        :param folderB: The TO folder to create
        :param init_actions: Create initial, dummy action object file
        :param archive: Add archive internal action if True
        """
        # Create actions object file
        if init_actions:
            for folder in [folderA]:
                # Sample external action
                actions = deepcopy(ActionsLauncher.ActionsObjectTpl)

                # Internal Archive action
                if archive:
                    actions['actions'].append(ActionsLauncher.ActionInternalSaveLocalArch)

                # Internal Distribute action
                distribAction = deepcopy(ActionsLauncher.ActionInternalDistribute)
                distribAction['args'] = ';'.join(folderB)
                actions['actions'].append(distribAction)

                # Save actions file
                with open(os.path.join(folder, 'actions.json'), 'w') as fact:
                    fact.write(json.dumps(actions, indent=4))

        # Launch monitoring
        qa = queue.Queue()
        dwThrA = define_dir_watcher(folderA, qa)
        self.queues.append({'from': folderA, 'to': folderB,
                            'this_folder_is': 'from',
                            'queue': qa, 'thread': dwThrA})
        self.dirWatchers.append(dwThrA)

    def createFolders(self, cfg : dict, create_folders=False):
        """
        Ensure the folders exist
        :param cfg: The configuration dictionary
        :param create_folders: True, to create IO folders
        :return: -
        """
        basePath = cfg['base_path']
        logger.info('SIS Controller Base Path: {}'.format(basePath))
        logger.info('Ensuring the SIS folders exist under base path')

        identifiers = dict(cfg['id'])

        ids = (identifiers if create_folders else {})

        # Create main folders, and read-me files
        for elem, acronym in ids.items():
            actualId = acronym.replace('_','/')
            for ep in ['in', 'out']:
                endPoint = '{}/{}/{}'.format(basePath, actualId, ep)
                self.createIfNotExists(endPoint)
            readmeFileName = '{}/{}/README.md'.format(basePath, actualId)
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

                circ = dataSpec['circulation']
                from_to = circ.split('=>')

                from_elem = from_to[0]
                fromId = identifiers[from_elem]
                inSrcElem = fromId.replace('_','/')
                fromEndPoint = '{}/in/{}'.format(inSrcElem, dataId)
                circSourceDir = os.path.join(basePath, fromEndPoint)
                if create_folders: self.createIfNotExists(circSourceDir)

                circTargetDirs = []
                toEndPoints = []
                for to_elem in from_to[1].split(','):
                    toId = identifiers[to_elem]
                    outSrcElem = toId.replace('_','/')
                    toEndPoint = '{}/out/{}'.format(outSrcElem, dataId)
                    circTargetDir = os.path.join(basePath, toEndPoint)
                    if create_folders: self.createIfNotExists(circTargetDir)

                    circTargetDirs.append(circTargetDir)
                    toEndPoints.append(toEndPoint)

                self.initMonitoring(circSourceDir, toEndPoints, \
                                    init_actions=create_folders, archive=True)

                logger.debug('>>> {}::{} : {} => {}'.format(flowName, datasetName,
                                                           fromEndPoint,
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
        self.createFolders(cfg=self.cfg, create_folders=self.create_folders)

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
