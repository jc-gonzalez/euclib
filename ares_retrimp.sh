#!/bin/bash 
#------------------------------------------------------------------------------------
# ares_retrimp.sh
# Launcher for ARES Retrieve/Import GUI tool
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
export PYARES_INI_FILE=/home/ares/.config/aresri/retrieval_config.ini
export PYTHONPATH=$(pwd) 
python3 ./apps/ares_retrimp/ares_retrimp.py

