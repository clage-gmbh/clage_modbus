clage_modbus_map = [{
("temp_in_C10", 0): ["ain", 0, "Current inlet temperature [1/10 deg centigrade]"],
("temp_out_C10", 0): ["ain", 1, "Current outlet temperature [1/10 deg centigrade]"],
("flow_lmin10", 0): ["ain", 2, "Current water flow [1/10 l/min]"],
("power_kW10", 0): ["ain", 3, "Current power consumption [1/10 kW]"],
("power_PC", 0): ["ain", 4, "Current power consumption [percent]"],
("total_energy_Wh", 0): ["ain", 100, "Total energy consumed 32 bit [Wh]"],
("total_volume_l", 0): ["ain", 102, "Total water consumed 32 bit [l]"],
("total_tap_count", 0): ["ain", 104, "Count of water tap usages 32 bit"],
("fill_remain_l", 0): ["ain", 200, "Remaining volume to fill liter"],
("fill_remain_s", 0): ["ain", 201, "Remaining time to fill seconds"],
("pu_error", 0): ["ain", 300, "Device error code (0 = no error)"],
("ctrl_val", 0): ["ain", 301, "Control value (normal value 2800)"],
("app_version", 0): ["ain", 350, "Application version string"],
("end", 0xC1A6): ["ain", 400, "Modbus register mapping minor version (const)"],
("end", 1): ["ain", 401, "Modbus register mapping version (const)"],
("end", 0): ["ain", 402, "Modbus register mapping minor version (const)"],
("epoch_s", 0): ["ain", 500, "Time of day as UNIX epoch 64 bit [s]"],
("temp_setpoint_C10", 0): ["aout", 0, "Outlet temperature setpoint [1/10 deg centigrade]"],
("flow_max_lmin10", 0): ["aout", 1, "Maximum volume per time at outlet [1/10 l/min]"],
("temp_setpoint_max_scalding_protection_C10", 0): ["aout", 2, "Maximum temperature setpoint [1/10 deg centigrade]"],
("modbus_baudrate", 0): ["aout", 400, "UART symbols per second for EIA-485 usage."],
("modbus_parity", 0): ["aout", 402, "UART parity (0:none; 1:odd; 2:even) for EIA-485."],
("modbus_server_addr", 0): ["aout", 403, "First server address"],
("modbus_server_addr", 1): ["aout", 404, "Second server address"],
("modbus_server_addr", 2): ["aout", 405, "Third server address"],
("modbus_server_addr", 3): ["aout", 406, "Fourth server address"],
("modbus_server_addr", 4): ["aout", 407, "Fifth server address"],
("modbus_broadcast_addr", 0): ["aout", 408, "DLE broadcast address"],
("modbus_epoch_s", 0): ["aout", 410, "DLE broadcast address"],
("wlan_ssid", 0): ["aout", 500, "WLAN SSID string"],
("is_power_limit", 0): ["din", 0, "Flag if this device is on power limit."],
("is_temp_setpoint_max", 0): ["din", 1, "Is setpoint at maximum"],
("is_temp_setpoint_max_scalding_protection", 0): ["din", 2, "Is scalding protection"],
("is_jumper_lock", 0): ["din", 3, "Flag if jumper lock is active"],
("is_therm_treat_inhibit", 0): ["din", 200, "Flag if thermal treatment is inhibited"],
("is_therm_treat_active", 0): ["din", 201, "Flag if thermal treatment is active"],
("filling_active", 0): ["din", 202, "Flag if tub filling is active."],
("is_fill_amount", 0): ["din", 203, "Flag if fill amount is given"],
("is_fill_time", 0): ["din", 204, "Flag if filling time is given"],
("has_RM", 0): ["din", 300, "Flag if this device has a radio module installed."],
("has_VC", 0): ["din", 301, "Flag if this device has a valve installed."],
("is_fast_boot", 0): ["din", 302, "Fast boot ???"],
("leakage", 0): ["din", 303, "Flag if leakage is detected"],
("vc_is_closed", 0): ["din", 304, "Flag if valve is closed"],
("net_sntp_client_up", 0): ["din", 500, "Flag if SNTP client is running"],
("wlan_sta_bssid_set", 0): ["din", 501, "Flag if WLAN BSSID is set"],
("hw_tft_touch", 0): ["din", 600, "Flag if this HW provides a TFT/GUI (DSX Touch)"],
("gui_screens_up", 0): ["din", 601, "Flag if all screens are up"],
("timer_do_stop_flow", 0): ["dout", 100, "Flag if timer shall stop flow"],
("timer_stop_if_flow0", 0): ["dout", 101, "Flag if timer shall stop at no flow"],
("system_do_reboot", 0): ["dout", 300, "Flag to trigger new start of CPU"],
("system_do_reset", 0): ["dout", 301, "Flag to trigger factory reset"],
("system_do_reboot_next", 0): ["dout", 302, "Flag to trigger start of second partition"],
("update_do_all", 0): ["dout", 310, "Flag to trigger complete online update"],
("update_use_beta", 0): ["dout", 311, "Flag if beta software shall be used"],
("update_do_check", 0): ["dout", 312, "Flag to trigger checking for update"],
("update_check_daily", 0): ["dout", 313, "Flag if daily check shall be performed"],
("update_do_app", 0): ["dout", 314, "Flag to trigger application download"],
("update_do_www", 0): ["dout", 315, "Flag to trigger web-UI content download"],
("modbus_test_init", 0): ["dout", 400, "Flag if initial test sequence shall be transmitted"],
("modbus_test", 0): ["dout", 401, "Flag if continuous test sequence shall be transmitted"],
("wlan_ap", 0): ["dout", 500, "Flag if WLAN shall operate as AP"],
("wlan_restart", 0): ["dout", 501, "Trigger WLAN restart"],
("wlan_setup", 0): ["dout", 502, "Trigger WLAN setup"],
("wlan_scan", 0): ["dout", 503, "Trigger WLAN scan"],
("wlan_active", 0): ["dout", 504, "Flag if WLAN shall be active"],
("net_sntp_from_dhcp", 0): ["dout", 505, "Flag if SNTP servers from DHCP shall be used."],
("daylight_saving", 0): ["dout", 506, "Flag if daylight saving shall be applied."],
("net_rest_api", 0): ["dout", 507, "Flag if REST API shall be started."],
("net_rest_api_tls", 0): ["dout", 508, "Flag if REST shall use TLS encryption."],
("net_rest_api_auth", 0): ["dout", 509, "Flag if REST shall check for authentication."],
("net_aws", 0): ["dout", 510, "AWS active (not implemented)"],
("net_matter_api", 0): ["dout", 511, "Matter active (not implemented)"],
("home_flow", 0): ["dout", 600, "Flag if home screen shall show flow limit"],
("home_time", 0): ["dout", 601, "Flag if home screen shall show time"],
("display_bright_flow", 0): ["dout", 602, "Water flow finish idle state of display light."],
("sound", 0): ["dout", 603, "Flag if device shall make sounds"],
("start_jingle", 0): ["dout", 604, "Flag if device shall play a start jingle"],
("stat_show_costs", 0): ["dout", 605, "Flag if consts shall be shown in statistics."],
("devel_log_cpu_temp", 0): ["dout", 700, "Flag if CPU temperature shall be logged."],
("devel_update_test_feed", 0): ["dout", 701, "Flag if developer test feed shall be used for update"],
}]
