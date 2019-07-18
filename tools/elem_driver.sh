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

usage() {
    echo "usage: $0 [ -h ] [ -c ] [ -i <elem-in-path> ] [ -o <elem-out-path> ]"
    echo "where:"
    echo "  -h         Show this message"
    echo "  -c         Create folders"
    echo "  -i <path>  Folder to get inputs from, for the element (SIS output)"
    echo "  -o <path>  Folder to put outputs to, for the element (SIS input)"
}

die () {
    echo "$2"
    exit $1
}

ELEM_IN_PATH=""
ELEM_OUT_PATH=""

# Parse command line Options
while getopts :hci:o: OPT; do
    case ${OPT} in
        h|+h) usage ;;
        c|+c) CREATE_FOLDERS="yes" ;;
        i|+i) ELEM_IN_PATH="$OPTARG" ;;
        o|+o) ELEM_OUT_PATH="$OPTARG" ;;
        *)    usage ; exit 2
    esac
done
shift `expr $OPTIND - 1`
OPTIND=1

echo ">>>>>> $*"

createFld=${CREATE_FOLDERS:=no}

# Ensure input, output, scratch and archive folders exist
if [ "$createFld" == "yes" ]; then
    mkdir -p ${THISDIR}/scratch ${THISDIR}/archive
    if [ -z "$ELEM_IN_PATH" ]; then
        rm -rf "${THISDIR}/in" ; mkdir -p "${THISDIR}/in"
    else
        ln -s "$ELEM_IN_PATH" "${THISDIR}/in"
    fi
    if [ -z "$ELEM_OUT_PATH" ]; then
        rm -rf "${THISDIR}/out" ; mkdir -p "${THISDIR}/out"
    else
        ln -s "$ELEM_OUT_PATH" "${THISDIR}/out"
    fi
else
    [ -d ${THISDIR}/out ]     || die 1 "Folder to place generated products not set"
    [ -d ${THISDIR}/in ]      || die 2 "Folder to gather input files not set"
    [ -d ${THISDIR}/scratch ] || die 3 "Scratch folder with seminal files not set"
    [ -d ${THISDIR}/archive ] || die 4 "Archive folder not set"
fi

python3 ${SCRIPTDIR}/elem_driver.py \
    -i ${THISDIR}/out -o ${THISDIR}/in \
    -I ${THISDIR}/scratch -O ${THISDIR}/archive \
    $*
