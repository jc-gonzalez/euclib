#!/bin/bash 
#------------------------------------------------------------------------------------
# sis_controller.sh
# Launcher for SIS Controller tool
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
SCRIPTPATH=$(dirname $(stat -f $0))
export PYTHONPATH=$SCRIPTPATH
python3 $SCRIPTPATH/apps/sis_controller/sis_controller.py $*

