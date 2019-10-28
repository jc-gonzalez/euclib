#!/bin/bash 
#------------------------------------------------------------------------------------
# launch_iot.sh
# Launcher for iot IO simulator
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
ICR_IOT_TO_SIS_DEST=$SISUSER@$SISHOST:$SISBASE/iot/in/cmd
ICR_IOT_TO_SIS_DIR=${SCRIPTPATH}/io/out/icd
mkdir -p ${ICR_IOT_TO_SIS_DIR}
cat <<-EOF >${ICR_IOT_TO_SIS_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": [ { "id": "send_to_soc_sis_ess", "type": "cmd",
                   "command": "$TRANSFER", "args": "{file_name} $ICR_IOT_TO_SIS_DEST"} ]
}
EOF

##---- Uplink chain

# -None-

##====== Local and Remote folders polling

# SSR files from SOC.ESS
python3 ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${ICR_IOT_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/iot_icr.log $SHOW_LOG_DEBUG &

##====== Element I/O GUI

python3 ${EUCLIB_PATH}/apps/simelem/simelem.py \
    -e IOT -f ${SCRIPTPATH}/io/arc \
    -i ${SCRIPTPATH}/io/in \
    -o SIS:${ICR_IOT_TO_SIS_DIR} \
    -l ${SCRIPTPATH}/iot_sim.log $SHOW_LOG_DEBUG &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/iot_{sim,icr}.log)
touch $LOGS

xterm $XTERM_LOG_OPTS -e multitail -F ~/bin/multitail.conf -cS log4j $LOGS && \
kill -- -$$


