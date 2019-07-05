#!/bin/bash 
#------------------------------------------------------------------------------------
# sis_controller.sh
# Launcher for SIS Controller tool
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
export PYTHONPATH=$(pwd)
python3 ./apps/sis_controller/sis_controller.py $*

