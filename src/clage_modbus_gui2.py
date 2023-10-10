#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Example how to use clage_modbus class for a GUI.
#
import clage_modbus
import tkinter as tk


class param_widget(tk.LabelFrame):
    '''Frame with a label inside showing a parameter'''

    def __init__(self, parent, param_name, frame_text):
        # Setup the frame we inherit
        tk.LabelFrame.__init__(self, parent, text=frame_text, padx=10, pady=10)
        # Keep parameter name and unit for update()
        self.param_name = param_name
        self.param_unit = c.get_base_unit(self.param_name)
        # Create a TK string as dynamic content of the label.
        self.str = tk.StringVar()
        self.str.set('--')
        # Create a label as child of this frame showing the TK string.
        self.label = tk.Label(self, textvariable=self.str,
                              font=("Helvetica", 24), fg="blue")
        # Inside the frame we use pack() for layout (outside grid())
        self.label.pack()
        # Let the first update happen in 0.5 seconds
        self.master.after(500, self.update)

    def update(self):
        # Ask for new value and convert to base unit.
        base = c.get_base_value(self.param_name, c.get_value(self.param_name))
        # Write value and unit to string that is displayed by label.
        self.str.set(f'{base} {self.param_unit}')
        # Next update in a second.
        self.master.after(1000, self.update)


# Create an object of class clage_modbus from module of the same name.
c = clage_modbus.clage_modbus()
# Read command line arguments
c.check_args()
# Connect to server with ID taken from command line
c.connect()

# Create a window (not a windows save us from that)
window = tk.Tk()
window.title("CLAGE")
for i in range(3):
    window.rowconfigure(i, weight=1)
for i in range(2):
    window.columnconfigure(i, weight=1)

# Create widget showing parameters as a sticky grid (table like)
setpoint = param_widget(window, 'temp_setpoint_C10', 'Setpoint')
setpoint.grid(row=0, column=0, sticky="nsew")
flow_max = param_widget(window, 'flow_max_lmin10', 'Flow Limit')
flow_max.grid(row=0, column=1, sticky="nsew")
temp_in = param_widget(window, 'temp_in_C10', 'Inlet Temp.')
temp_in.grid(row=1, column=0, sticky="nsew")
temp_out = param_widget(window, 'temp_out_C10', 'Outlet Temp.')
temp_out.grid(row=1, column=1, sticky="nsew")
flow = param_widget(window, 'flow_lmin10', 'Water Flow')
flow.grid(row=2, column=0, sticky="nsew")
power = param_widget(window, 'power_kW10', 'Power')
power.grid(row=2, column=1, sticky="nsew")

# Operate the GUI main loop
if c.args.verbose:
    print('start main loop of GUI')
window.mainloop()

# EOF
