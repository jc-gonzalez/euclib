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

if [ $# -lt 1 ]; then
    echo "usage: "
    echo "        $0 gui "
    echo "        $0 retrieve <options>"
    exit 0
fi

case $1 in
    gui)
        python3 ${SCRIPTPATH}/apps/ares_retrimp/ares_retrimp_gui.py
        ;;
    retrieve)
        shift
        python3 ${SCRIPTPATH}/apps/ares_retrimp/ares_retrimp.py $*
        ;;
     *)
        echo "Command not understood: $1"
        exit 1
        ;;
esac
