#!/bin/bash 
#------------------------------------------------------------------------------------
# ares_retrimp.sh
# Launcher for LE1 (VIS & NISP) Metadata enhancer
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
export PYARES_INI_FILE=/home/ares/.config/aresri/retrieval_config.ini
export PYTHONPATH=$(pwd) 
python3 ./apps/le1_enhance/le1_enhance.py $*


