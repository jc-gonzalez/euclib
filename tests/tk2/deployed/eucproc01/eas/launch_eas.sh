#!/bin/bash 
#------------------------------------------------------------------------------------
# launch-eas.sh
# Launcher for EAS IO simulator
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

##---- Uplink/Downlink chain
EAS_INBOX_DIR=${SCRIPTPATH}/io/in
mkdir -p ${EAS_INBOX_DIR}
cat <<-EOF >${EAS_INBOX_DIR}/actions.json
{
    "last_update": "",
    "history": [ "Initial creation" ],
    "actions": []
}
EOF

##====== Local and Remote folders polling

# Any file to anywhere to EAS
$PYTHON ${EUCLIB_PATH}/apps/watch_folder/watch_folder.py \
    -D ${EAS_INBOX_DIR} \
    -l ${SCRIPTPATH}/eas_in.log .log $SHOW_LOG_DEBUG  &

##====== Log monitoring

sleep 1

LOGS=$(echo ${SCRIPTPATH}/eas_in.log)
touch $LOGS

$SHOW_LOGS $LOGS && \
kill -- -$$
