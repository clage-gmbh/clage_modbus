#!/bin/bash
#

export BUS_ID=97
export CM="./clage_modbus.py -s $BUS_ID"

echo
echo "Read temperature setting:"
$CM -r temp_setpoint_C10

echo
echo "Write temperature setting:"
$CM -w temp_setpoint_C10=39.5

echo
echo "Write raw temperature setting:"
$CM -w temp_setpoint_C10:385

echo
echo "List parameters with totals:"
$CM --list | grep total

echo
echo "Read temperature setting and flow limit:"
$CM -r temp_setpoint_C10 -r flow_max_lmin10

echo
echo "Read temperature setting and flow limit:"
$CM -r temp_setpoint_C10 flow_max_lmin10

echo
echo "Set temperature and flow limit:"
$CM -w temp_setpoint_C10=41.5 -w flow_max_lmin10=9.5

echo
echo "Read temperature and set:"
$CM -r temp_setpoint_C10 -w temp_setpoint_C10=40.5

echo
echo "Run a sequence:"
$CM -R temp_setpoint_C10=45.5 wait:1s temp_setpoint_C10=35 wait:1s

echo
echo "Run a sequence with aliases:"
$CM -a t=temp_setpoint_C10 -a f=flow_max_lmin10 -R t=45.5 t f=8 f w:.25s t=35 t f=10 f w:.25s

echo
echo "Read all parameters to CSV"
$CM --read list --format csv --timestamp iso >clage_modbus_test.csv

#EOF