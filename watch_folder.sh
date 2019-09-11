#!/bin/bash 
#------------------------------------------------------------------------------------
# watch_folder.sh
# Launcher for Watch Folder script
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
SCRIPTPATH=$(dirname $(stat -f $0))
export PYTHONPATH=$SCRIPTPATH
python3 $SCRIPTPATH/apps/watch_folder/watch_folder.py -D $(pwd) $*
