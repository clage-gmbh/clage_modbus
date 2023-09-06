#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Example how to use clage_modbus class for a GUI.
#
import clage_modbus
import tkinter as tk

param_name = 'temp_setpoint_C10'


def update_temp():
    # Ask for new value and convert to base unit.
    base = c.get_base_value(param_name, c.get_value(param_name))
    # Write value and unit to string that is displayed by label.
    temp_str.set(f'{base} {param_unit}')
    # Next update in a second.
    window.after(1000, update_temp)


# Create an object of class clage_modbus from module of the same name.
c = clage_modbus.clage_modbus()
# Read command line arguments
c.check_args()
# Connect to server with ID taken from command line
c.connect()
param_unit = c.get_base_unit(param_name)

# Create a window (not a windows save us from that)
window = tk.Tk()
window.title("CLAGE")
# Nice frame around.
frame = tk.LabelFrame(window, text="Setpoint", padx=10, pady=10)
# Create a TK string variable
temp_str = tk.StringVar()
temp_str.set('--')
# Create a label inside the window showing that string
label = tk.Label(frame, textvariable=temp_str,
                 font=("Helvetica", 24), fg="blue")
label.pack()
frame.pack()
# Let the temperature update in a second.
window.after(500, update_temp)
# Operate the GUI main loop
if c.args.verbose:
    print('start main loop of GUI')
window.mainloop()

# EOF
