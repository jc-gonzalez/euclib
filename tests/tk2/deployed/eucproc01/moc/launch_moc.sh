#!/bin/bash 
#------------------------------------------------------------------------------------
# launch-moc.sh
# Launcher for MOC IO simulator
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
SSR_FROM_SOC_TO_MOC_DIR=${SCRIPTPATH}/io/in/ssr
mkdir -p ${SSR_FROM_SOC_TO_MOC_DIR}
cat <<-EOF >${SSR_FROM_SOC_TO_MOC_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": []
}
EOF

##---- Downlink chain
EDDS_MOC_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/moc/in/edds
EDDS_MOC_TO_SIS_DIR=${SCRIPTPATH}/io/out/edds
mkdir -p ${EDDS_MOC_TO_SIS_DIR}
cat <<-EOF >${EDDS_MOC_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_hms", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $EDDS_MOC_TO_SIS_DEST"} ]
}
EOF

SCI_MOC_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/moc/in/sci
SCI_MOC_TO_SIS_DIR=${SCRIPTPATH}/io/out/sci
mkdir -p ${SCI_MOC_TO_SIS_DIR}
cat <<-EOF >${SCI_MOC_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_le1", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $SCI_MOC_TO_SIS_DEST" } ]
}
EOF

##====== Local and Remote folders polling

# SSR files from SOC.ESS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${SSR_FROM_SOC_TO_MOC_DIR} \
    -R ${SISUSER}@${SISHOST}:${SISBASE}/moc/out/ssr \
    -l ${SCRIPTPATH}/moc_ssr.log $SHOW_LOG_DEBUG &

# EDDS files to SOC[SIS].HMS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${EDDS_MOC_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/moc_edds.log $SHOW_LOG_DEBUG &

# SCI files to SOC[SIS].LE1
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${SCI_MOC_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/moc_sci.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI

$PYTHON ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e MOC -f ${SCRIPTPATH}/io/arc \
    -i ${SSR_FROM_SOC_TO_MOC_DIR} \
    -o HMS:${EDDS_MOC_TO_SIS_DIR},LE1:${SCI_MOC_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/moc_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/moc_{sim,ssr,edds,sci}.log)
touch $LOGS

$SHOW_LOGS $LOGS && \
kill -- -$$
