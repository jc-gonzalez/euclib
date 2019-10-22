#!/bin/bash 
#------------------------------------------------------------------------------------
# ares_retrimp.sh
# Launcher for ARES Retrieve/Import GUI tool
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
SCRIPTPATH=$(dirname $(stat -f $0))
export PYARES_INI_FILE=/home/ares/.config/aresri/retrieval_config.ini
export PYTHONPATH=${SCRIPTPATH} 
python3 ${SCRIPTPATH}/apps/ares_retrimp/ares_retrimp.py

