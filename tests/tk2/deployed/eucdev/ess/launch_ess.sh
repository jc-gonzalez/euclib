#!/bin/bash 
#------------------------------------------------------------------------------------
# launch-ess.sh
# Launcher for ESS IO simulator
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
SRV_FROM_SOC_TO_ESS_DIR=${SCRIPTPATH}/io/in/srv
SRV_FROM_SOC_TO_ESS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/ess/out/srv
mkdir -p ${SRV_FROM_SOC_TO_ESS_DIR}
cat <<-EOF >${SRV_FROM_SOC_TO_ESS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": []
}
EOF

OSS_TO_SIS_DIR=${SCRIPTPATH}/io/out/oss
OSS_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/soc/ess/in/oss
mkdir -p ${OSS_TO_SIS_DIR}
cat <<-EOF >${OSS_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_ess", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $OSS_TO_SIS_DEST"} ]
}
EOF

##====== Local and Remote folders polling

# SRV files from IOT to SOC.ESS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${SRV_FROM_SOC_TO_ESS_DIR} \
    -R ${SRV_FROM_SOC_TO_ESS_DEST} \
    -l ${SCRIPTPATH}/ess_srv.log $SHOW_LOG_DEBUG &

# OSS files from SOC.ESS to SIS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${OSS_TO_SIS_DIR} \
    -R ${OSS_TO_SIS_DEST} \
    -l ${SCRIPTPATH}/ess_oss.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI

$PYTHON ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e ESS -f ${SCRIPTPATH}/io/arc \
    -i ${SRV_FROM_SOC_TO_ESS_DIR} \
    -o SIS:${OSS_TO_SIS_DEST} \
    -l ${SCRIPTPATH}/ess_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/ess_{sim,srv,oss}.log)
touch $LOGS

$SHOW_LOGS $LOGS && \
kill -- -$$
