#!/bin/bash 
#------------------------------------------------------------------------------------
# elem_driver.sh
# Driver to emulate elements that product and consume different products
#
# Created by J C Gonzalez <jcgonzalez@sciops.esa.int>
# Copyright (C) 2019 by Euclid SOC Team
#------------------------------------------------------------------------------------
THISDIR=$(pwd)
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null && pwd )"
export PYTHONPATH=$(basename "$SCRIPTDIR")

createFld=${CREATE_FOLDERS:=no}

die () {
    echo "$2"
    exit $1
}

echo $(pwd)

# Ensure input, output, scratch and archive folders exist
if [ "$CREATE_FOLDERS" == "yes" ]; then
    mkdir -p \
        ${THISDIR}/out \
        ${THISDIR}/in \
        ${THISDIR}/scratch \
        ${THISDIR}/archive
else
    [ -d ${THISDIR}/out ]     || die 1 "Folder to place generated products not set"
    [ -d ${THISDIR}/in ]      || die 2 "Folder to gather input files not set"
    [ -d ${THISDIR}/scratch ] || die 3 "Scratch folder with seminal files not set"
    [ -d ${THISDIR}/archive ] || die 4 "Archive folder not set"
fi

python3 $SCRIPTDIR/elem_driver.py \
    -i ${THISDIR}/out -o ${THISDIR}/in -I ${THISDIR}/scratch -O ${THISDIR}/archive \
    $*

