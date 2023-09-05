#!/bin/bash
#
# Temperature ramp by TCP-Modbus gateway
#

# Config gateway to use
export CLAGE_MODBUS_IP_ADDR=192.168.5.160
# Config server ID of CLAGE device
export CLAGE_MODBUS_SERVER_ID=97
# Config name of parameter
PARAM=temp_setpoint_C10

trap "echo 'Ramp stopped'; exit" SIGINT

while true
do
    for temp in {20..60}
    do
        ./clage_modbus.py -R ${PARAM}=${temp} wait:1s ${PARAM}
    done
done

#EOF
