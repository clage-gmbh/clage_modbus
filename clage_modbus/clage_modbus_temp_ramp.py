#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Example how to use clage_modbus class for more complex sequences.
#
import clage_modbus

# Create an object of class clage_modbus from module of the same name.
c = clage_modbus.clage_modbus()
# Read command line arguments
c.check_args()
# Connect to server with ID taken from command line
c.connect()
# Valid interval
minmax = (20.0, 60.0)
# Start temperature
temp = minmax[0]
# Increase
while True:
    c.set_any(f'temp_setpoint_C10={temp}')
    c.do_step(f'wait:500ms')
    temp = temp+1.0 if temp+1.0 <= minmax[1] else minmax[0]

# EOF
