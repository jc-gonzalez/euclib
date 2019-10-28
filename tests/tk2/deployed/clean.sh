#!/bin/bash 
#------------------------------------------------------------------------------------
# clean.sh
# Clean this directory
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
SCRIPTPATH=$(cd $(dirname $0); pwd; cd - > /dev/null)
export PYTHONPATH=$EUCLIB_PATH

find . -name .DS_Store -exec rm {} \;

for io in $(find . -name io); do
    rm -rf ${io}/in/* ${io}/out/* ${io}/arc/*
done
