#!/bin/bash 
#------------------------------------------------------------------------------------
# launch_ecsrv.sh
# Launcher for ecsrv IO simulator
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
RDS_ECSRV_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/ecsrv/in/srv
RDS_ECSRV_TO_SIS_DIR=${SCRIPTPATH}/io/out/rds
mkdir -p ${RDS_ECSRV_TO_SIS_DIR}
cat <<-EOF >${RDS_ECSRV_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_ess", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $RDS_ECSRV_TO_SIS_DEST"} ]
}
EOF

##---- Uplink chain

# -None-

##====== Local and Remote folders polling

# SSR files from SOC.ESS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${RDS_ECSRV_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/ecsrv_rds.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI

$PYTHON ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e ECSRV -f ${SCRIPTPATH}/io/arc \
    -i ${SCRIPTPATH}/io/in \
    -o SIS:${RDS_ECSRV_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/ecsrv_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/ecsrv_{sim,rds}.log)
touch $LOGS

$SHOW_LOGS $LOGS && \
kill -- -$$


