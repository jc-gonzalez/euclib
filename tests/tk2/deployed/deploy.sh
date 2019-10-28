#!/bin/bash 
#------------------------------------------------------------------------------------
# deploy.sh
# Deploys specific folder for a given machine
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
if [ -z "${EUCLIB_PATH}" ]; then
    echo "You should set the env.var. EUCLIB_PATH"
    exit 1
fi

SCRIPTPATH=$(cd $(dirname $0); pwd; cd - > /dev/null)
export PYTHONPATH=$EUCLIB_PATH

machine=$1
remote=$2

ssh $remote mkdir -p tk2/deployed
scp -r ${SCRIPTPATH}/$machine/* $remote:tk2/deployed/
scp -r ${SCRIPTPATH}/env.src $remote:tk2/deployed/
