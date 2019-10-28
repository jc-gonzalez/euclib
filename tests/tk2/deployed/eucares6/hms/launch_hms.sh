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
HKTM_HMS_FROM_SIS_DIR=${SCRIPTPATH}/io/in/edds
HKTM_HMS_FROM_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/hms/out/edds
mkdir -p ${HKTM_HMS_FROM_SIS_DIR}
HKTM_HMS_IMPORT_DIR=$HOME/ARES_RUNTIME/import/eddsBinary/TM
cat <<-EOF >${HKTM_HMS_FROM_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "import_data", "type": "cmd",
                   "command": "tar", "args": "xvzf {file_name} $HKTM_HMS_IMPORT_DIR"},
                 { "id": "generate_hktm", "type": "cmd",
                   "command": "echo", "args": "Generate HKTM from {file_name}" } ]
}
EOF

HKTM_HMS_TO_SIS_DIR=${SCRIPTPATH}/io/out/edds
HKTM_HMS_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/hms/in/hktm
mkdir -p ${HKTM_HMS_TO_SIS_DIR}
cat <<-EOF >${HKTM_HMS_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_hktm_prod", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $HKTM_HMS_TO_SIS_DEST"} ]
}
EOF

LE1_HMS_FROM_SIS_DIR=${SCRIPTPATH}/io/in/le1
LE1_HMS_FROM_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/hms/out/le1
mkdir -p ${LE1_HMS_FROM_SIS_DIR}
cat <<-EOF >${LE1_HMS_FROM_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "get_le1", "type": "cmd",
                   "command": "echo", "args": "Enhance LE1 product {file_name}" } ]
}
EOF

LE1_HMS_TO_SIS_DIR=${SCRIPTPATH}/io/out/le1
LE1_HMS_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/hms/in/le1e
mkdir -p ${LE1_HMS_TO_SIS_DIR}
cat <<-EOF >${LE1_HMS_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_le1enh", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $LE1_HMS_TO_SIS_DEST" } ]
}
EOF

QLA_HMS_FROM_SIS_DIR=${SCRIPTPATH}/io/in/qla
QLA_HMS_FROM_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/hms/out/qla
mkdir -p ${QLA_HMS_FROM_SIS_DIR}
cat <<-EOF >${QLA_HMS_FROM_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "get_qla_report", "type": "cmd",
                   "command": "echo", "args": "Parse and ingest QLA report {file_name}" } ]
}
EOF

##====== Remote folders polling

# EDDS files to SOC[SIS].HMS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${HKTM_HMS_FROM_SIS_DIR} \
    -R ${HKTM_HMS_FROM_SIS_DEST} \
    -l ${SCRIPTPATH}/hms_edds.log $SHOW_LOG_DEBUG &

# HKTM files to SOC[SIS]
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${HKTM_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_hktm.log $SHOW_LOG_DEBUG &

# LE1 files to SOC[SIS].HMS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${LE1_HMS_FROM_SIS_DIR} \
    -R ${LE1_HMS_FROM_SIS_DEST} \
    -l ${SCRIPTPATH}/hms_le1.log $SHOW_LOG_DEBUG &

# LE1 enh files to SOC[SIS]
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${LE1_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_le1e.log $SHOW_LOG_DEBUG &

# QLA files to SOC[SIS].HMS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${QLA_HMS_FROM_SIS_DIR} \
    -R ${QLA_HMS_FROM_SIS_DEST} \
    -l ${SCRIPTPATH}/hms_qla.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI

python3 ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e HMS -f ${SCRIPTPATH}/io/arc \
    -i ${HKTM_HMS_FROM_SIS_DIR},${LE1_HMS_FROM_SIS_DIR},${QLA_HMS_FROM_SIS_DIR} \
    -o HMS:${HKTM_HMS_TO_SIS_DIR},LE1:${LE1_HMS_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/hms_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/hms_{sim,edds,hktm,le1,le1e,qla}.log)
touch $LOGS

#xterm $XTERM_LOG_OPTS -e multitail -F ~/bin/multitail.conf -cS log4j $LOGS && \
tail -f $LOGS && \
kill -- -$$
