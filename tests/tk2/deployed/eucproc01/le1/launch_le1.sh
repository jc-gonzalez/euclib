#!/bin/bash 
#------------------------------------------------------------------------------------
# launch-le1.sh
# Launcher for LE1 IO simulator
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
SCI_SIS_TO_LE1_DIR=${SCRIPTPATH}/io/in/sci
mkdir -p ${SCI_SIS_TO_LE1_DIR}
cat <<-EOF >${SCI_SIS_TO_LE1_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": []
}
EOF

LE1_LE1_TO_SIS_DIR=${SCRIPTPATH}/io/out/le1
LE1_LE1_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/le1/in/le1
mkdir -p ${LE1_LE1_TO_SIS_DIR}
cat <<-EOF >${LE1_LE1_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_le1_to_sis", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $LE1_LE1_TO_SIS_DEST"" } ]
}
EOF

QLA_TO_SIS_DIR=${SCRIPTPATH}/io/out/le1
QLA_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/qla/in/qla
mkdir -p ${QLA_TO_SIS_DIR}
cat <<-EOF >${QLA_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_le1_to_sis", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $QLA_TO_SIS_DEST"" } ]
}
EOF

##====== Local and Remote folders polling

# SCI files from SIS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${SCI_SIS_TO_LE1_DIR} \
    -R ${SISUSER}@${SISHOST}:${SISBASE}/le1/out/sci \
    -l ${SCRIPTPATH}/le1_sci.log $SHOW_LOG_DEBUG &

# LE1 files for HMS (SIS)
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${LE1_LE1_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/le1_le1.log $SHOW_LOG_DEBUG &

# QLA files for HMS (SIS)
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${QLA_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/le1_qla.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI
QLA_TO_HMS_DIR=${SCRIPTPATH}/io/out/qla
$PYTHON ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e LE1 -f $HOME/qpf/data/archive \
    -i ${SCI_SIS_TO_LE1_DIR} \
    -o HMS:${QLA_TO_HMS} \
    -l ${SCRIPTPATH}/le1_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/le1_{sim,sci,le1,qla}.log)
touch $LOGS

$SHOW_LOGS $LOGS && \
kill -- -$$
