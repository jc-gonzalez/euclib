#!/bin/bash 
#------------------------------------------------------------------------------------
# launch-hms.sh
# Launcher for HMS IO simulator
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

rm -rf *.log

## Prepare actions in io/out (Element I/O simulation)

##---- Uplink chain

# -None-

##---- Downlink chain
mkdir -p ${SCRIPTPATH}/io/out/hktm
HKTM_HMS_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE
HKTM_HMS_TO_SIS_DIR=${SCRIPTPATH}/io/out/edds
cat <<-EOF >${HKTM_HMS_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_hms", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $HKTM_HMS_TO_SIS_DEST"} ]
}
EOF

mkdir -p ${SCRIPTPATH}/io/out/le1
LE1_HMS_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE
LE1_HMS_TO_SIS_DIR=${SCRIPTPATH}/io/out/le1
cat <<-EOF >${LE1_HMS_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_le1", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $LE1_HMS_TO_SIS_DEST" } ]
}
EOF

mkdir -p ${SCRIPTPATH}/io/out/qla
QLA_HMS_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE
QLA_HMS_TO_SIS_DIR=${SCRIPTPATH}/io/out/qla
cat <<-EOF >${QLA_HMS_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_le1", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $QLA_HMS_TO_SIS_DEST" } ]
}
EOF

##====== Remote folders polling

# EDDS files to SOC[SIS].HMS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${EDDS_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_hktm.log $SHOW_LOG_DEBUG &

# LE1 files to SOC[SIS].HMS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${LE1_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_le1.log $SHOW_LOG_DEBUG &

# QLA files to SOC[SIS].HMS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${QLA_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_qla.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI

python3 ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e HMS -f ${SCRIPTPATH}/io/arc \
    -i ${SSR_FROM_SOC_TO_HMS_DIR} \
    -o HMS:${EDDS_HMS_TO_SIS_DIR},LE1:${SCI_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/hms_{sim,hktm,le1,qla}.log)
touch $LOGS

xterm $XTERM_LOG_OPTS -e multitail -F ~/bin/multitail.conf -cS log4j $LOGS && \
kill -- -$$
