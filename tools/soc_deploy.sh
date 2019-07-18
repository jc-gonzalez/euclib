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
EUCLIB=$(dirname "$SCRIPTDIR")
EUCLIBTOOLS=${EUCLIB}/tools
EUCLIBAPPS=${EUCLIB}/apps

PYTHON=python3
ELEM_DRIVER=${EUCLIBTOOLS}/elem_driver.py

export PYTHONPATH=${EUCLIB}

#- Messages
STEP=0

#- Options
SOC_PATH="$HOME/SOC"
SIS_IF_FROM=""
REUSE=""
CREATE="no"

#- Other
SCRIPTNAME=$(basename $0)
DATE=$(date +"%Y%m%d%H%M%S")
LOG_FILE="${THISDIR}/soc_emul_${DATE}.log"

############################################################
###### Handy functions
############################################################

VERSION=1.0

greetings () {
    say "==============================================================================="
    say " Euclid SOC Emulation Test Deployment"
    say " Version ${VERSION}"
    say " Date: ${DATE}"
    say "==============================================================================="
    say ""
}

usage () {
    local opts1="[ -h ] [ -s <path> ] [ -i <path> ] [ -c ]"
    say "Usage: ${SCRIPTNAME} $opts1"
    say ""
    say "where:"
    say "  -h         Show this usage message"
    say "  -s <path>  SOC Tree to be placed at <path> (default:$SOC_PATH)"
    say "  -i <path>  Folder that holds an instance of the SOC Interface System "
    say "             directory tree (default:$SOC_PATH/SIS/IF) to be replicated"
    say "  -c         Create element driver folders (default:no)"
    say ""
    exit 1
}

say () {
    echo -e "$*"
    echo -e "$*" >> "${LOG_FILE}"
}

step () {
    say "## STEP ${STEP} - $*"
    STEP=$(($STEP + 1))
}

die () {
    ec=$1
    shift
    say "ERROR: $*"
    exit ${ec}
}

create_elem_emu_dir () {
    local name=$1
    local pth="${SOC_PATH}/${name}"
    mkdir -p "${pth}/scratch"
    touch "${pth}/scratch/Product_YYY_XXXXX.dat"
    echo "${pth}"
}

trap 'cleanup' 2

cleaunp() {
  echo "Caught SIGINT, cleanning up . . ."
  kill $(ps -o pid= --ppid $$)
  exit 1
}

############################################################
###### Start
############################################################

##==== Parse command line
while getopts :hs:i:c OPT; do
    case ${OPT} in
        h|+h) usage ;;
        s|+s) SOC_PATH="$OPTARG" ;;
        i|+i) SIS_IF_FROM="$OPTARG"; REUSE="-r" ;;
        c|+c) CREATE="yes" ;;
        *)    usage ; exit 2
    esac
done
shift `expr $OPTIND - 1`
OPTIND=1

##==== Say hello
greetings

##==== Deploy components ===================================
export PATH=${SCRIPTDIR}:$PATH
export CREATE_FOLDERS=${CREATE}
mkdir -p ${SOC_PATH}

#--- Create element driver folders
IOT_PATH=$(create_elem_emu_dir IOT)
MOC_PATH=$(create_elem_emu_dir MOC)
ECSRV_PATH=$(create_elem_emu_dir ECSRV)
ESS_PATH=$(create_elem_emu_dir ESS)
SCS_PATH=$(create_elem_emu_dir SCS)
EAS_PATH=$(create_elem_emu_dir EAS)
HMS_PATH=$(create_elem_emu_dir HMS)
QLA_PATH=$(create_elem_emu_dir QLA)
LE1_PATH=$(create_elem_emu_dir LE1)

#--- Deploy SIS --------------------------------------------
SIS_PATH="${SOC_PATH}/SIS"
mkdir -p "${SIS_PATH}"
if [ -n "${SIS_IF_FROM}" ]; then
    mv "${SIS_PATH}" "${SOC_PATH}/SIS.orig.${DATE}"
    cp -r "${SIS_IF_FROM}" "${SIS_PATH}"
fi

ORIG_CFG_FILE="${EUCLIB}/sis/soc-if-spec.json"
CFG_FILE="${THISDIR}/soc-if-spec.${DATE}.json"
cp "${ORIG_CFG_FILE}" "${CFG_FILE}"
sed -i .orig \
    -e "s#\"base_path\": \".*\",#\"base_path\": \"$SIS_PATH\",#g" \
    "${CFG_FILE}"

${PYTHON} ${EUCLIBAPPS}/sis_controller/sis_controller.py \
    -c "${CFG_FILE}" ${REUSE} -d &

sleep 1
#exit 0

#--- Deploy IOT driver -------------------------------------
cd "${IOT_PATH}"
${PYTHON} ${ELEM_DRIVER} -n IOT \
    -i cmd:${IOT_PATH}/in.cmd:${SIS_PATH}/iot/in/cmd \
    -i iot:${IOT_PATH}/in.iot:${SIS_PATH}/iot/in/iot \
    -o ${IOT_PATH}/out \
    -I ${IOT_PATH}/scratch -O ${IOT_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy MOC driver -------------------------------------
cd "${MOC_PATH}"
${PYTHON} ${ELEM_DRIVER} -n MOC \
    -i sci:${MOC_PATH}/in.sci:${SIS_PATH}/moc/in/sci \
    -i data:${MOC_PATH}/in.data:${SIS_PATH}/moc/in/data \
    -i edds:${MOC_PATH}/in.edds:${SIS_PATH}/moc/in/edds \
    -o iot:${MOC_PATH}/out.iot:${SIS_PATH}/moc/out/iot \
    -o ssr:${MOC_PATH}/out.ssr:${SIS_PATH}/moc/out/ssr \
    -I ${MOC_PATH}/scratch -O ${MOC_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy ECSurv driver ----------------------------------
cd "${ECSRV_PATH}"
${PYTHON} ${ELEM_DRIVER} -n ECSurv \
    -i srv:${ECSRV_PATH}/in.srv:${SIS_PATH}/ecsrv/in/srv \
    -o ${ECSRV_PATH}/out \
    -I ${ECSRV_PATH}/scratch -O ${ECSRV_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy ESS driver -------------------------------------
cd "${ESS_PATH}"
${PYTHON} ${ELEM_DRIVER} -n ESS \
    -i evt:${ESS_PATH}/in.evt:${SIS_PATH}/soc/ess/in/evt \
    -i ssr:${ESS_PATH}/in.ssr:${SIS_PATH}/soc/ess/in/ssr \
    -i oss:${ESS_PATH}/in.oss:${SIS_PATH}/soc/ess/in/oss \
    -o ossq:${ESS_PATH}/out.ossq:${SIS_PATH}/soc/ess/out/ossq \
    -o cmd:${ESS_PATH}/out.cmd:${SIS_PATH}/soc/ess/out/cmd \
    -o data:${ESS_PATH}/out.data:${SIS_PATH}/soc/ess/out/data \
    -o srv:${ESS_PATH}/out.srv:${SIS_PATH}/soc/ess/out/srv \
    -I ${ESS_PATH}/scratch -O ${ESS_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy SCS driver -------------------------------------
cd "${SCS_PATH}"
${PYTHON} ${ELEM_DRIVER} -n SCS \
    -i scs:${SCS_PATH}/in:${SIS_PATH}/soc/scs/in \
    -o cmd:${SCS_PATH}/out.cmd:${SIS_PATH}/soc/scs/out/cmd \
    -o evt:${SCS_PATH}/out.evt:${SIS_PATH}/soc/scs/out/evt \
    -o ssr:${SCS_PATH}/out.ssr:${SIS_PATH}/soc/scs/out/ssr \
    -o data:${SCS_PATH}/out.data:${SIS_PATH}/soc/scs/out/data \
    -I ${SCS_PATH}/scratch -O ${SCS_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy EAS driver -------------------------------------
cd "${EAS_PATH}"
${PYTHON} ${ELEM_DRIVER} -n EAS \
    -i ossq:${EAS_PATH}/in.ossq:${SIS_PATH}/soc/eas/in/ossq \
    -o sgsio:${EAS_PATH}/out.sgsio:${SIS_PATH}/soc/eas/out/sgsio \
    -o qla:${EAS_PATH}/out.qla:${SIS_PATH}/soc/eas/out/qla \
    -o iot:${EAS_PATH}/out.iot:${SIS_PATH}/soc/eas/out/iot \
    -o oss:${EAS_PATH}/out.oss:${SIS_PATH}/soc/eas/out/oss \
    -o le1:${EAS_PATH}/out.le1:${SIS_PATH}/soc/eas/out/le1 \
    -o data:${EAS_PATH}/out.data:${SIS_PATH}/soc/eas/out/data \
    -o srv:${EAS_PATH}/out.srv:${SIS_PATH}/soc/eas/out/srv \
    -I ${EAS_PATH}/scratch -O ${EAS_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy HMS driver -------------------------------------
cd "${HMS_PATH}"
${PYTHON} ${ELEM_DRIVER} -n HMS \
    -i edds:${HMS_PATH}/in.le1:${SIS_PATH}/soc/hms/in/edds \
    -o qla:${HMS_PATH}/out.sci:${SIS_PATH}/soc/hms/out/qla \
    -o edds:${HMS_PATH}/out.edds:${SIS_PATH}/soc/hms/out/edds \
    -I ${HMS_PATH}/scratch -O ${HMS_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy LE1 driver -------------------------------------
cd "${LE1_PATH}"
${PYTHON} ${ELEM_DRIVER} -n LE1 \
    -i le1:${LE1_PATH}/in.le1:${SIS_PATH}/soc/le1/in/le1 \
    -o sci:${LE1_PATH}/out.sci:${SIS_PATH}/soc/le1/out/sci \
    -o edds:${LE1_PATH}/out.edds:${SIS_PATH}/soc/le1/out/edds \
    -I ${LE1_PATH}/scratch -O ${LE1_PATH}/archive -c 1 -t 1. -d &
cd -

#--- Deploy QLA driver -------------------------------------
cd "${QLA_PATH}"
${PYTHON} ${ELEM_DRIVER} -n QLA \
    -i qla:${QLA_PATH}/in.qla:${SIS_PATH}/soc/qla/in/qla \
    -o le1:${QLA_PATH}/out.le1:${SIS_PATH}/soc/qla/out/le1 \
    -o ssr:${QLA_PATH}/out.ssr:${SIS_PATH}/soc/qla/out/ssr \
    -I ${QLA_PATH}/scratch -O ${QLA_PATH}/archive -c 1 -t 1. -d &
cd -

##==== Show monitors ===================================

WDTH=122
HGHT=31
DX=630
DY=310
X=0
Y=0
MAXX=$(( 1900 - DX ))
MAXY=$(( 1200 - DY ))

for fld in  ${IOT_PATH} ${MOC_PATH} ${ECSRV_PATH} \
            ${ESS_PATH} ${SCS_PATH} ${EAS_PATH} \
            ${HMS_PATH} ${QLA_PATH} ${LE1_PATH} ; do

    elem=$(basename ${fld})

    # Open new terminal
    xterm -fn '-*-clean-medium-*-*-*-8-*-75-75-*-50-*-*' \
        -bg black -fg green -cr red \
        -geometry ${WDTH}x${HGHT}+${X}+${Y} -title ${elem} \
        -e ${EUCLIBTOOLS}/monitor-folder.sh ${fld} &
    #& xtp=$!
    #xty=$(ps -o tty $(( xtp + 1 )) | tail -1)

    # Launch monitor script, and redirect output to terminal TTY
    #bash ${EUCLIBTOOLS}/monitor-folder.sh $elem /dev/$xty &

    # Update coordinates
    X=$(( X + DX ))
    if [ ${X} -gt ${MAXX} ]; then
        X=0
        Y=$(( Y + DY ))
        if [ ${Y} -gt ${MAXY} ]; then
            break
        fi
    fi

done

echo "System launched."

while : ; do sleep 1; done

exit 0
