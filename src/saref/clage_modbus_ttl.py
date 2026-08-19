#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create a SAREF-oriented OWL Turtle mapping from the CLAGE Modbus/RTU table."""

from __future__ import annotations

import csv
import re
from decimal import Decimal
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD


CSV_FILE = Path("../clage_modbus_tab.csv")
TTL_FILE = Path("clage_modbus_tab.ttl")

SAREF = Namespace("https://saref.etsi.org/core/")
S4ENER = Namespace("https://saref.etsi.org/saref4ener/")
S4SYST = Namespace("https://saref.etsi.org/saref4syst/")
S4WATR = Namespace("https://saref.etsi.org/saref4watr/")
CLAGE = Namespace("https://clage.de/ontology/")
MODBUS = Namespace("https://clage.de/ontology/modbus/")
DEVICE = Namespace("https://clage.de/device/")
UNIT = Namespace("https://clage.de/ontology/unit/")

DEVICE_INSTANCE = DEVICE.CLAGE_Instantaneous_Water_Heater
REGISTER_MAP = MODBUS.CLAGE_Modbus_Register_Map

REGISTER_CLASS = {
    "input register": MODBUS.InputRegister,
    "holding register": MODBUS.HoldingRegister,
    "coil": MODBUS.Coil,
    "contact": MODBUS.DiscreteInput,
}

SIGNAL_CLASS = {
    "ain": MODBUS.AnalogInputSignal,
    "aout": MODBUS.AnalogOutputSignal,
    "din": MODBUS.DigitalInputSignal,
    "dout": MODBUS.DigitalOutputSignal,
}

UNIT_LABELS = {
    "none": None,
    "s": "second",
    "min": "minute",
    "l": "litre",
    "Wh": "watt hour",
    "PC": "percent",
    "epoch": "Unix epoch second",
    "C10": "degree Celsius, scaled by 10",
    "C10main": "degree Celsius, scaled by 10",
    "C10max": "degree Celsius, scaled by 10",
    "kW10": "kilowatt, scaled by 10",
    "lmin10": "litre per minute, scaled by 10",
    "lmin10max": "litre per minute, scaled by 10",
    "8Ohmcm": "8 ohm centimetre",
    "u16ctrl": "control value",
    "u8mpsid": "MPS identifier",
    "parity": "parity code",
    "sound": "sound identifier",
}

UNIT_SEMANTICS = {
    "C10": {
        "engineering_unit": "degree Celsius",
        "scale_factor": Decimal("0.1"),
        "scale_divisor": Decimal("10"),
    },
    "C10main": {
        "engineering_unit": "degree Celsius",
        "scale_factor": Decimal("0.1"),
        "scale_divisor": Decimal("10"),
    },
    "C10max": {
        "engineering_unit": "degree Celsius",
        "scale_factor": Decimal("0.1"),
        "scale_divisor": Decimal("10"),
    },
    "kW10": {
        "engineering_unit": "kilowatt",
        "scale_factor": Decimal("0.1"),
        "scale_divisor": Decimal("10"),
    },
    "lmin10": {
        "engineering_unit": "litre per minute",
        "scale_factor": Decimal("0.1"),
        "scale_divisor": Decimal("10"),
    },
    "lmin10max": {
        "engineering_unit": "litre per minute",
        "scale_factor": Decimal("0.1"),
        "scale_divisor": Decimal("10"),
    },
}

DATA_TYPES = {
    "bool": XSD.boolean,
    "u8": XSD.unsignedByte,
    "u16": XSD.unsignedShort,
    "u32": XSD.unsignedInt,
    "u64": XSD.unsignedLong,
    "i16": XSD.short,
}

SEMANTIC_PROFILES = {
    "app2_v_ma_mi_re": {
        "classes": (CLAGE.DeviceIdentificationProperty, CLAGE.SoftwareVersionProperty),
        "role": CLAGE.InactiveSoftwareVersionRole,
        "quantity_kind": CLAGE.SoftwareVersion,
        "extension_terms": (S4ENER.firmwareVersion, S4WATR.hasFirmwareVersion),
        "observed": True,
    },
    "app_v_ma_mi_re": {
        "classes": (CLAGE.DeviceIdentificationProperty, CLAGE.SoftwareVersionProperty),
        "role": CLAGE.ActiveSoftwareVersionRole,
        "quantity_kind": CLAGE.SoftwareVersion,
        "extension_terms": (S4ENER.firmwareVersion, S4WATR.hasFirmwareVersion),
        "observed": True,
    },
    "article_number_u64": {
        "classes": (CLAGE.DeviceIdentificationProperty, CLAGE.ArticleNumberProperty),
        "role": CLAGE.IdentificationRole,
        "quantity_kind": CLAGE.ArticleNumber,
        "extension_terms": (S4ENER.deviceCode,),
        "observed": True,
    },
    "device_total_heating_s": {
        "classes": (CLAGE.OperatingTimeProperty, CLAGE.CounterProperty),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.HeatingTime,
        "extension_terms": (S4WATR.MeterOperatingTime,),
        "observed": True,
    },
    "device_total_uptime_s": {
        "classes": (CLAGE.OperatingTimeProperty, CLAGE.CounterProperty),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.OperatingTime,
        "extension_terms": (S4WATR.MeterOnTime,),
        "observed": True,
    },
    "device_uptime_s": {
        "classes": (CLAGE.OperatingTimeProperty, CLAGE.DiagnosticProperty),
        "role": CLAGE.CurrentRuntimeRole,
        "quantity_kind": CLAGE.OperatingTimeSincePowerOn,
        "extension_terms": (S4WATR.MeterOnTime,),
        "observed": True,
    },
    "fill_remain_l": {
        "classes": (CLAGE.FillAutomaticProperty, CLAGE.FlowVolumeProperty),
        "role": CLAGE.RemainingValueRole,
        "quantity_kind": CLAGE.FillVolume,
        "property_kind": S4WATR.FlowVolume,
        "observed": True,
    },
    "fill_remain_s": {
        "classes": (CLAGE.FillAutomaticProperty, CLAGE.DurationProperty),
        "role": CLAGE.RemainingValueRole,
        "quantity_kind": CLAGE.FillDuration,
        "extension_terms": (S4ENER.hasRemainingSlotTime,),
        "observed": True,
    },
    "filling_active": {
        "classes": (CLAGE.FillAutomaticProperty, CLAGE.ControlInputProperty),
        "role": CLAGE.ActivationRole,
        "quantity_kind": CLAGE.FillAutomaticActivation,
        "controlled": True,
    },
    "flow_lmin10": {
        "classes": (CLAGE.FlowRateProperty, CLAGE.MeasuredValueProperty),
        "role": CLAGE.MeasuredValueRole,
        "quantity_kind": CLAGE.FlowRate,
        "property_kind": S4WATR.FlowRate,
        "observed": True,
        "maximum_property": CLAGE.flow_max_lmin10,
    },
    "flow_max_delta_steps": {
        "classes": (CLAGE.FlowRateProperty, CLAGE.RelativeAdjustmentProperty),
        "role": CLAGE.AdjustmentRole,
        "quantity_kind": CLAGE.FlowRateAdjustment,
        "affects_property": S4WATR.FlowRate,
        "adjusts_property": CLAGE.flow_max_lmin10,
        "equivalent_panel_function": "CLAGE flow limit + and - buttons",
        "positive_delta_effect": "writing a positive value increases the maximum flow-rate limit by that many CLAGE steps",
        "negative_delta_effect": "writing a negative value decreases the maximum flow-rate limit by that many CLAGE steps",
        "step_engineering_unit": "litre per minute",
        "fine_step_engineering_value": Decimal("0.5"),
        "fine_step_min_engineering_value": Decimal("4.5"),
        "fine_step_max_engineering_value": Decimal("10.0"),
        "coarse_step_engineering_value": Decimal("1.0"),
        "coarse_step_min_engineering_value": Decimal("10.0"),
        "coarse_step_max_engineering_value": Decimal("14.0"),
        "controlled": True,
    },
    "flow_max_lmin10": {
        "classes": (CLAGE.FlowRateProperty, CLAGE.LimitProperty),
        "role": CLAGE.LimitRole,
        "quantity_kind": CLAGE.FlowRate,
        "property_kind": S4WATR.FlowRate,
        "constrains_property": CLAGE.flow_lmin10,
        "controlled": True,
        "min_engineering_value": Decimal("4.5"),
        "max_engineering_value": Decimal("14.0"),
        "min_raw_value": Decimal("45"),
        "max_raw_value": Decimal("140"),
        "step_engineering_unit": "litre per minute",
        "fine_step_engineering_value": Decimal("0.5"),
        "fine_step_min_engineering_value": Decimal("4.5"),
        "fine_step_max_engineering_value": Decimal("10.0"),
        "coarse_step_engineering_value": Decimal("1.0"),
        "coarse_step_min_engineering_value": Decimal("10.0"),
        "coarse_step_max_engineering_value": Decimal("14.0"),
        "special_values": (
            {
                "resource": CLAGE["value/flow_max_lmin10/auto"],
                "raw_value": Decimal("254"),
                "engineering_value": Decimal("25.4"),
                "display_label": "AUTO",
                "meaning": "automatic flow reduction is enabled when the requested outlet temperature cannot otherwise be maintained",
                "prioritizes_property": CLAGE.temp_setpoint_C10,
            },
            {
                "resource": CLAGE["value/flow_max_lmin10/max"],
                "raw_value": Decimal("255"),
                "engineering_value": Decimal("25.5"),
                "display_label": "MAX",
                "meaning": "the valve is fully opened and no flow-rate limitation is applied",
                "disables_limitation_of_property": CLAGE.flow_lmin10,
            },
        ),
    },
    "has_VC": {
        "classes": (CLAGE.ValveProperty, CLAGE.AvailabilityStatusProperty),
        "role": CLAGE.AvailabilityRole,
        "quantity_kind": CLAGE.ValvePresence,
        "feature": CLAGE.ControllableValve,
        "presence_of": CLAGE.ControllableValve,
        "enables_control_of_properties": (CLAGE.flow_max_lmin10,),
        "enables_limitation_of_properties": (CLAGE.flow_lmin10,),
        "enables_power_reduction_by_properties": (CLAGE.flow_max_lmin10,),
        "observed": True,
    },
    "has_RM": {
        "classes": (CLAGE.RadioModuleProperty, CLAGE.AvailabilityStatusProperty),
        "role": CLAGE.AvailabilityRole,
        "quantity_kind": CLAGE.RadioModulePresence,
        "feature": CLAGE.RadioModule,
        "presence_of": CLAGE.RadioModule,
        "enables_communication_protocol": CLAGE.Bluetooth,
        "compatible_control_clients": (
            CLAGE.FX3RemoteControl,
            CLAGE.FXNextRemoteControl,
            CLAGE.CLAGESmartControlApp,
        ),
        "observed": True,
    },
    "is_fill_amount": {
        "classes": (CLAGE.FillAutomaticProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.FillByVolumeActive,
        "extension_terms": (S4ENER.FillRateBasedProfile, S4WATR.FlowVolume),
        "observed": True,
    },
    "is_fill_time": {
        "classes": (CLAGE.FillAutomaticProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.FillByTimeActive,
        "extension_terms": (S4ENER.Timer,),
        "observed": True,
    },
    "is_temp_setpoint_max": {
        "classes": (CLAGE.TemperatureProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.Temperature,
        "affects_property": S4WATR.FlowTemperature,
        "observed": True,
    },
    "is_temp_setpoint_max_scalding_protection": {
        "classes": (CLAGE.TemperatureProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.Temperature,
        "affects_property": S4WATR.FlowTemperature,
        "observed": True,
    },
    "is_therm_treat_active": {
        "classes": (CLAGE.ThermalTreatmentProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.ThermalTreatmentActive,
        "affects_property": S4WATR.FlowTemperature,
        "observed": True,
    },
    "is_therm_treat_inhibit": {
        "classes": (CLAGE.ThermalTreatmentProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.ThermalTreatmentInhibited,
        "affects_property": S4WATR.FlowTemperature,
        "observed": True,
    },
    "leakage": {
        "classes": (CLAGE.LeakageDetectionProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.WaterPresenceInDeviceHousing,
        "observed": True,
    },
    "leakage_active": {
        "classes": (CLAGE.LeakageDetectionProperty, CLAGE.ThresholdProperty),
        "role": CLAGE.ThresholdRole,
        "quantity_kind": CLAGE.WaterPresenceInDeviceHousing,
        "controlled": True,
    },
    "leakage_inactive": {
        "classes": (CLAGE.LeakageDetectionProperty, CLAGE.ThresholdProperty),
        "role": CLAGE.ThresholdRole,
        "quantity_kind": CLAGE.WaterPresenceInDeviceHousing,
        "controlled": True,
    },
    "leakage_raw": {
        "classes": (CLAGE.LeakageDetectionProperty, CLAGE.MeasuredValueProperty),
        "role": CLAGE.MeasuredValueRole,
        "quantity_kind": CLAGE.WaterPresenceInDeviceHousing,
        "observed": True,
    },
    "mps0_kW10": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.InstallationConfigurationProperty),
        "role": CLAGE.InstallationConfigurationRole,
        "quantity_kind": CLAGE.ElectricPower,
        "property_kind": S4ENER.NominalPowerLimit,
    },
    "mps1_kW10": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.InstallationConfigurationProperty),
        "role": CLAGE.InstallationConfigurationRole,
        "quantity_kind": CLAGE.ElectricPower,
        "property_kind": S4ENER.NominalPowerLimit,
    },
    "mps2_kW10": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.InstallationConfigurationProperty),
        "role": CLAGE.InstallationConfigurationRole,
        "quantity_kind": CLAGE.ElectricPower,
        "property_kind": S4ENER.NominalPowerLimit,
    },
    "mps3_kW10": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.InstallationConfigurationProperty),
        "role": CLAGE.InstallationConfigurationRole,
        "quantity_kind": CLAGE.ElectricPower,
        "property_kind": S4ENER.NominalPowerLimit,
    },
    "mps_id": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.InstallationConfigurationProperty),
        "role": CLAGE.InstallationConfigurationRole,
        "quantity_kind": CLAGE.PowerLevelSelection,
        "property_kind": S4ENER.PowerLimit,
    },
    "mps_id_end": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.InstallationConfigurationProperty),
        "role": CLAGE.InstallationConfigurationRole,
        "quantity_kind": CLAGE.PowerLevelCount,
        "property_kind": S4ENER.PowerLimit,
    },
    "modbus_server_addr": {
        "classes": (CLAGE.ModbusConfigurationProperty, CLAGE.ModbusServerAddressProperty),
        "role": CLAGE.AddressRole,
        "quantity_kind": CLAGE.ModbusServerAddress,
        "controlled": True,
        "primary_modbus_server_address": True,
        "currently_supported": True,
        "default_address_derived_from": CLAGE.serial_number_u64,
        "zero_serial_suffix_default_address": 100,
    },
    "modbus_word_order_big_endian": {
        "classes": (CLAGE.ModbusConfigurationProperty, CLAGE.ModbusWordOrderProperty),
        "role": CLAGE.ConfigurationRole,
        "quantity_kind": CLAGE.BigEndianWordOrder,
        "controlled": True,
        "currently_supported": True,
        "applies_to_multiple_register_values": True,
    },
    "modbus_server_addr_1": {
        "classes": (
            CLAGE.ModbusConfigurationProperty,
            CLAGE.ModbusServerAddressProperty,
            CLAGE.UnsupportedAlternativeProperty,
        ),
        "role": CLAGE.UnsupportedAlternativeRole,
        "quantity_kind": CLAGE.ModbusServerAddress,
        "currently_supported": False,
    },
    "modbus_server_addr_2": {
        "classes": (
            CLAGE.ModbusConfigurationProperty,
            CLAGE.ModbusServerAddressProperty,
            CLAGE.UnsupportedAlternativeProperty,
        ),
        "role": CLAGE.UnsupportedAlternativeRole,
        "quantity_kind": CLAGE.ModbusServerAddress,
        "currently_supported": False,
    },
    "modbus_server_addr_3": {
        "classes": (
            CLAGE.ModbusConfigurationProperty,
            CLAGE.ModbusServerAddressProperty,
            CLAGE.UnsupportedAlternativeProperty,
        ),
        "role": CLAGE.UnsupportedAlternativeRole,
        "quantity_kind": CLAGE.ModbusServerAddress,
        "currently_supported": False,
    },
    "modbus_server_addr_4": {
        "classes": (
            CLAGE.ModbusConfigurationProperty,
            CLAGE.ModbusServerAddressProperty,
            CLAGE.UnsupportedAlternativeProperty,
        ),
        "role": CLAGE.UnsupportedAlternativeRole,
        "quantity_kind": CLAGE.ModbusServerAddress,
        "currently_supported": False,
    },
    "power_PC": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.MeasuredValueProperty),
        "role": CLAGE.MeasuredValueRole,
        "quantity_kind": CLAGE.PowerUtilization,
        "observed": True,
    },
    "power_kW10": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.MeasuredValueProperty),
        "role": CLAGE.MeasuredValueRole,
        "quantity_kind": CLAGE.ElectricPower,
        "property_kind": S4ENER.ElectricPower3PhaseSymmetric,
        "observed": True,
        "maximum_property": CLAGE.power_max_kW10,
    },
    "power_max_kW10": {
        "classes": (CLAGE.ElectricPowerProperty, CLAGE.LimitProperty),
        "role": CLAGE.LimitRole,
        "quantity_kind": CLAGE.ElectricPower,
        "property_kind": S4ENER.NominalPowerLimit,
        "observed": True,
        "constrains_property": CLAGE.power_kW10,
    },
    "temp_in_C10": {
        "classes": (CLAGE.TemperatureProperty, CLAGE.MeasuredValueProperty),
        "role": CLAGE.MeasuredValueRole,
        "quantity_kind": CLAGE.Temperature,
        "property_kind": S4WATR.FlowTemperature,
        "feature": CLAGE.ColdWaterInlet,
        "observed": True,
    },
    "temp_out_C10": {
        "classes": (CLAGE.TemperatureProperty, CLAGE.MeasuredValueProperty),
        "role": CLAGE.MeasuredValueRole,
        "quantity_kind": CLAGE.Temperature,
        "property_kind": S4WATR.FlowTemperature,
        "feature": CLAGE.HotWaterOutlet,
        "observed": True,
    },
    "temp_setpoint_C10": {
        "classes": (CLAGE.TemperatureProperty, CLAGE.SetpointProperty),
        "role": CLAGE.SetpointRole,
        "quantity_kind": CLAGE.Temperature,
        "property_kind": S4WATR.FlowTemperature,
        "feature": CLAGE.HotWaterOutlet,
        "controlled": True,
        "disabled_engineering_value": Decimal("19.0"),
        "min_engineering_value": Decimal("20.0"),
        "max_engineering_value": Decimal("60.0"),
        "maximum_property": CLAGE.temp_setpoint_max_scalding_protection_C10,
        "thermal_treatment_engineering_value": Decimal("70.0"),
    },
    "temp_setpoint_delta_steps": {
        "classes": (CLAGE.TemperatureProperty, CLAGE.RelativeAdjustmentProperty),
        "role": CLAGE.AdjustmentRole,
        "quantity_kind": CLAGE.TemperatureAdjustment,
        "property_kind": S4WATR.FlowTemperature,
        "feature": CLAGE.HotWaterOutlet,
        "adjusts_property": CLAGE.temp_setpoint_C10,
        "controlled": True,
        "equivalent_panel_function": "CLAGE temperature + and - buttons",
        "positive_delta_effect": "writing a positive value increases the temperature setpoint by that many CLAGE steps",
        "negative_delta_effect": "writing a negative value decreases the temperature setpoint by that many CLAGE steps",
        "step_engineering_unit": "kelvin",
        "coarse_step_engineering_value": Decimal("1.0"),
        "fine_step_engineering_value": Decimal("0.5"),
        "fine_step_min_engineering_value": Decimal("35.0"),
        "fine_step_max_engineering_value": Decimal("43.0"),
    },
    "temp_setpoint_max_scalding_protection_C10": {
        "classes": (
            CLAGE.TemperatureProperty,
            CLAGE.LimitProperty,
            CLAGE.ScaldingProtectionProperty,
        ),
        "role": CLAGE.LimitRole,
        "quantity_kind": CLAGE.Temperature,
        "property_kind": S4WATR.FlowTemperature,
        "feature": CLAGE.HotWaterOutlet,
        "constrains_property": CLAGE.temp_setpoint_C10,
        "controlled": True,
    },
    "therm_treat_active": {
        "classes": (CLAGE.ThermalTreatmentProperty, CLAGE.ControlInputProperty),
        "role": CLAGE.ActivationRole,
        "quantity_kind": CLAGE.ThermalTreatmentActivation,
        "affects_property": S4WATR.FlowTemperature,
        "controlled": True,
        "thermal_treatment_engineering_value": Decimal("70.0"),
    },
    "therm_treat_amount_l": {
        "classes": (
            CLAGE.ThermalTreatmentProperty,
            CLAGE.FlowVolumeProperty,
            CLAGE.CounterProperty,
        ),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.ThermalTreatmentVolume,
        "property_kind": S4WATR.FlowVolume,
        "observed": True,
    },
    "therm_treat_count": {
        "classes": (CLAGE.ThermalTreatmentProperty, CLAGE.CounterProperty),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.ThermalTreatmentCount,
        "observed": True,
    },
    "therm_treat_duration_s": {
        "classes": (CLAGE.ThermalTreatmentProperty, CLAGE.DurationProperty),
        "role": CLAGE.CurrentOrLastMeasurementRole,
        "quantity_kind": CLAGE.ThermalTreatmentDuration,
        "extension_terms": (S4ENER.hasDuration,),
        "observed": True,
    },
    "timer_active": {
        "classes": (CLAGE.TimerProperty, CLAGE.ControlInputProperty),
        "role": CLAGE.ActivationRole,
        "quantity_kind": CLAGE.TimerActivation,
        "extension_terms": (S4ENER.Timer,),
        "controlled": True,
    },
    "timer_do_stop_flow": {
        "classes": (CLAGE.TimerProperty, CLAGE.ControlInputProperty),
        "role": CLAGE.ControlInputRole,
        "quantity_kind": CLAGE.TimerStopFlowAction,
        "affects_property": S4WATR.FlowRate,
        "controlled": True,
    },
    "timer_start_s": {
        "classes": (CLAGE.TimerProperty, CLAGE.DurationProperty, CLAGE.SetpointProperty),
        "role": CLAGE.SetpointRole,
        "quantity_kind": CLAGE.TimerDuration,
        "extension_terms": (S4ENER.hasDuration,),
        "controlled": True,
    },
    "timer_stop_if_flow0": {
        "classes": (CLAGE.TimerProperty, CLAGE.ControlInputProperty),
        "role": CLAGE.ControlInputRole,
        "quantity_kind": CLAGE.TimerStopIfNoFlowCondition,
        "affects_property": S4WATR.FlowRate,
        "controlled": True,
    },
    "timer_timeout_min": {
        "classes": (CLAGE.TimerProperty, CLAGE.DurationProperty, CLAGE.LimitProperty),
        "role": CLAGE.TimeoutRole,
        "quantity_kind": CLAGE.TimerNoFlowTimeout,
        "extension_terms": (S4ENER.hasDuration,),
        "controlled": True,
    },
    "total_energy_Wh": {
        "classes": (CLAGE.EnergyProperty, CLAGE.CounterProperty),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.ElectricEnergy,
        "property_kind": S4ENER.Energy,
        "observed": True,
    },
    "total_tap_count": {
        "classes": (CLAGE.TapCountProperty, CLAGE.CounterProperty),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.TapCount,
        "observed": True,
    },
    "total_volume_l": {
        "classes": (CLAGE.FlowVolumeProperty, CLAGE.CounterProperty),
        "role": CLAGE.CounterRole,
        "quantity_kind": CLAGE.FlowVolume,
        "property_kind": S4WATR.FlowVolume,
        "observed": True,
    },
    "valve_open": {
        "classes": (CLAGE.ValveProperty, CLAGE.ControlInputProperty),
        "role": CLAGE.ControlInputRole,
        "quantity_kind": CLAGE.ValveOpening,
        "controlled": True,
    },
    "vc_is_closed": {
        "classes": (CLAGE.ValveProperty, CLAGE.StatusProperty),
        "role": CLAGE.StatusRole,
        "quantity_kind": CLAGE.ValveClosedState,
        "observed": True,
    },
    "volume_start_l": {
        "classes": (CLAGE.FillAutomaticProperty, CLAGE.FlowVolumeProperty, CLAGE.SetpointProperty),
        "role": CLAGE.SetpointRole,
        "quantity_kind": CLAGE.FillVolume,
        "property_kind": S4WATR.FlowVolume,
        "controlled": True,
    },
    "serial_number_u64": {
        "classes": (CLAGE.DeviceIdentificationProperty, CLAGE.SerialNumberProperty),
        "role": CLAGE.IdentificationRole,
        "quantity_kind": CLAGE.SerialNumber,
        "extension_terms": (S4ENER.serialNumber, S4WATR.hasFabricationNumber),
        "identifies_device": True,
        "observed": True,
    },
}

SAREF_EXTENSION_MAPPINGS = {
    "app2_v_ma_mi_re": (S4ENER.firmwareVersion, S4WATR.hasFirmwareVersion),
    "app_v_ma_mi_re": (S4ENER.firmwareVersion, S4WATR.hasFirmwareVersion),
    "article_number_u64": (S4ENER.deviceCode,),
    "device_total_heating_s": (S4WATR.MeterOperatingTime,),
    "device_total_uptime_s": (S4WATR.MeterOnTime,),
    "device_uptime_s": (S4WATR.MeterOnTime,),
    "fill_remain_l": (S4WATR.FlowVolume,),
    "fill_remain_s": (S4ENER.hasRemainingSlotTime,),
    "flow_lmin10": (S4WATR.FlowRate,),
    "flow_max_lmin10": (S4WATR.FlowRate,),
    "is_fill_amount": (S4ENER.FillRateBasedProfile, S4WATR.FlowVolume),
    "is_fill_time": (S4ENER.Timer,),
    "is_power_limit": (S4ENER.PowerLimit,),
    "is_temp_setpoint_max": (S4WATR.FlowTemperature,),
    "is_temp_setpoint_max_scalding_protection": (S4WATR.FlowTemperature,),
    "is_therm_treat_active": (S4WATR.FlowTemperature,),
    "is_therm_treat_inhibit": (S4WATR.FlowTemperature,),
    "mps0_kW10": (S4ENER.ElectricPower3PhaseSymmetric, S4ENER.NominalPowerLimit),
    "mps1_kW10": (S4ENER.ElectricPower3PhaseSymmetric, S4ENER.NominalPowerLimit),
    "mps2_kW10": (S4ENER.ElectricPower3PhaseSymmetric, S4ENER.NominalPowerLimit),
    "mps3_kW10": (S4ENER.ElectricPower3PhaseSymmetric, S4ENER.NominalPowerLimit),
    "mps_id": (S4ENER.PowerLimit,),
    "mps_id_end": (S4ENER.PowerLimit,),
    "power_PC": (S4ENER.ElectricPower3PhaseSymmetric, S4ENER.Consumption),
    "power_kW10": (S4ENER.ElectricPower3PhaseSymmetric, S4ENER.Consumption),
    "power_max_kW10": (
        S4ENER.ElectricPower3PhaseSymmetric,
        S4ENER.NominalPowerLimit,
    ),
    "resistivity_8Ohmcm": (S4WATR.Conductivity,),
    "resistivity_state": (S4WATR.Conductivity,),
    "serial_number_u64": (S4ENER.serialNumber, S4WATR.hasFabricationNumber),
    "temp_in_C10": (S4WATR.FlowTemperature,),
    "temp_out_C10": (S4WATR.FlowTemperature,),
    "temp_setpoint_C10": (S4WATR.FlowTemperature,),
    "temp_setpoint_delta_steps": (S4WATR.FlowTemperature,),
    "temp_setpoint_max_scalding_protection_C10": (S4WATR.FlowTemperature,),
    "therm_treat_active": (S4WATR.FlowTemperature,),
    "therm_treat_amount_l": (S4WATR.FlowVolume,),
    "therm_treat_count": (S4WATR.FlowTemperature,),
    "therm_treat_duration_s": (S4ENER.hasDuration,),
    "timer_active": (S4ENER.Timer,),
    "timer_do_stop_flow": (S4WATR.FlowRate,),
    "timer_start_s": (S4ENER.hasDuration,),
    "timer_stop_if_flow0": (S4WATR.FlowRate,),
    "timer_timeout_min": (S4ENER.hasDuration,),
    "total_energy_Wh": (S4ENER.Energy,),
    "total_tap_count": (S4WATR.FlowVolume,),
    "total_volume_l": (S4WATR.FlowVolume,),
    "volume_start_l": (S4WATR.FlowVolume,),
}

SAREF_EXTENSION_PROPERTY_CLASSES = {
    S4ENER.Energy: SAREF.Property,
    S4WATR.Conductivity: S4WATR.AcceptabilityProperty,
    S4WATR.FlowRate: S4WATR.WaterFlowProperty,
    S4WATR.FlowTemperature: S4WATR.WaterFlowProperty,
    S4WATR.FlowVolume: S4WATR.WaterFlowProperty,
}


def local_name(value: str) -> str:
    """Return an IRI-safe local name while preserving readable identifiers."""
    value = value.strip()
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unnamed"


def property_name(row: dict[str, str]) -> str:
    name = local_name(row["Parameter name"])
    exemplar = row["Parameter exemplar"].strip()
    if exemplar and exemplar != "0":
        return f"{name}_{exemplar}"
    return name


def clage_resource(kind: str, prop_local: str) -> URIRef:
    return CLAGE[f"{kind}/{prop_local}"]


def modbus_resource(kind: str, prop_local: str) -> URIRef:
    return MODBUS[f"{kind}/{prop_local}"]


def add_literal(
    graph: Graph,
    subject: URIRef,
    predicate: URIRef,
    value: str,
    datatype: URIRef | None = None,
) -> None:
    value = value.strip()
    if value:
        graph.add((subject, predicate, Literal(value, datatype=datatype)))


def raw_value_literal(value: object) -> Literal:
    if isinstance(value, Decimal) and value == value.to_integral_value():
        return Literal(int(value), datatype=XSD.integer)
    if isinstance(value, int):
        return Literal(value, datatype=XSD.integer)
    return Literal(value, datatype=XSD.decimal)


def add_schema(graph: Graph) -> None:
    graph.add((CLAGE.ModbusRegisterMapOntology, RDF.type, OWL.Ontology))
    for ontology in (SAREF, S4ENER, S4SYST, S4WATR):
        graph.add((CLAGE.ModbusRegisterMapOntology, OWL.imports, URIRef(str(ontology))))
    graph.add(
        (
            CLAGE.ModbusRegisterMapOntology,
            RDFS.label,
            Literal("CLAGE Modbus table mapped to SAREF", lang="en"),
        )
    )

    graph.add((CLAGE.InstantaneousWaterHeater, RDF.type, SAREF.DeviceKind))
    graph.add(
        (
            CLAGE.InstantaneousWaterHeater,
            RDFS.label,
            Literal("Electric instantaneous domestic hot water heater", lang="en"),
        )
    )
    graph.add((CLAGE.InstantaneousWaterHeater, SAREF.hasManufacturer, Literal("CLAGE", lang="en")))
    graph.add((CLAGE.InstantaneousWaterHeater, SAREF.hasModel, Literal("ISX", lang="en")))
    graph.add((CLAGE.InstantaneousWaterHeater, S4ENER.deviceName, Literal("ISX", lang="en")))
    graph.add((CLAGE.InstantaneousWaterHeater, S4ENER.vendorName, Literal("CLAGE", lang="en")))
    graph.add((CLAGE.InstantaneousWaterHeater, SAREF.consumes, CLAGE.Electricity))
    graph.add((CLAGE.InstantaneousWaterHeater, SAREF.produces, CLAGE.DomesticHotWater))

    graph.add((CLAGE.DomesticHotWaterInfrastructure, RDF.type, S4WATR.WaterInfrastructure))
    graph.add(
        (
            CLAGE.DomesticHotWaterInfrastructure,
            RDFS.label,
            Literal("domestic hot water infrastructure", lang="en"),
        )
    )
    graph.add((CLAGE.DomesticHotWaterInfrastructure, S4WATR.isDesignedFor, S4WATR.DrinkingWater))
    graph.add((CLAGE.DomesticHotWaterInfrastructure, S4WATR.isIntendedFor, S4WATR.Domestic))
    graph.add((CLAGE.DomesticHotWaterInfrastructure, S4SYST.hasSubSystem, DEVICE_INSTANCE))

    graph.add((DEVICE_INSTANCE, RDF.type, SAREF.Appliance))
    graph.add((DEVICE_INSTANCE, RDF.type, SAREF.Actuator))
    graph.add((DEVICE_INSTANCE, RDF.type, SAREF.Sensor))
    graph.add((DEVICE_INSTANCE, RDF.type, SAREF.Device))
    graph.add((DEVICE_INSTANCE, RDF.type, S4WATR.WaterDevice))
    graph.add((DEVICE_INSTANCE, SAREF.hasDeviceKind, CLAGE.InstantaneousWaterHeater))
    graph.add((DEVICE_INSTANCE, SAREF.hasManufacturer, Literal("CLAGE", lang="en")))
    graph.add((DEVICE_INSTANCE, SAREF.hasModel, Literal("ISX", lang="en")))
    graph.add((DEVICE_INSTANCE, S4ENER.deviceName, Literal("ISX", lang="en")))
    graph.add((DEVICE_INSTANCE, S4ENER.vendorName, Literal("CLAGE", lang="en")))
    graph.add((DEVICE_INSTANCE, SAREF.consumes, CLAGE.Electricity))
    graph.add((DEVICE_INSTANCE, SAREF.produces, CLAGE.DomesticHotWater))
    graph.add((DEVICE_INSTANCE, CLAGE.hasWaterInlet, CLAGE.ColdWaterInlet))
    graph.add((DEVICE_INSTANCE, CLAGE.hasWaterOutlet, CLAGE.HotWaterOutlet))
    graph.add(
        (
            DEVICE_INSTANCE,
            RDFS.label,
            Literal("CLAGE instantaneous domestic hot water heater", lang="en"),
        )
    )

    graph.add((REGISTER_MAP, RDF.type, CLAGE.ModbusRegisterMap))
    graph.add((REGISTER_MAP, CLAGE.describesDevice, DEVICE_INSTANCE))
    graph.add((REGISTER_MAP, RDFS.label, Literal("CLAGE Modbus register map", lang="en")))

    for cls, label in [
        (CLAGE.ModbusRegisterMap, "Modbus register map"),
        (CLAGE.MeasuredValueProperty, "measured value property"),
        (CLAGE.SetpointProperty, "setpoint property"),
        (CLAGE.LimitProperty, "limit property"),
        (CLAGE.ThresholdProperty, "threshold property"),
        (CLAGE.StatusProperty, "status property"),
        (CLAGE.DiagnosticProperty, "diagnostic property"),
        (CLAGE.ControlInputProperty, "control input property"),
        (CLAGE.RelativeAdjustmentProperty, "relative adjustment property"),
        (CLAGE.CounterProperty, "counter property"),
        (CLAGE.InstallationConfigurationProperty, "installation configuration property"),
        (CLAGE.AvailabilityStatusProperty, "availability status property"),
        (CLAGE.TemperatureProperty, "temperature property"),
        (CLAGE.FlowRateProperty, "flow rate property"),
        (CLAGE.FlowVolumeProperty, "flow volume property"),
        (CLAGE.DurationProperty, "duration property"),
        (CLAGE.ElectricPowerProperty, "electric power property"),
        (CLAGE.EnergyProperty, "energy property"),
        (CLAGE.OperatingTimeProperty, "operating time property"),
        (CLAGE.TimerProperty, "timer property"),
        (CLAGE.FillAutomaticProperty, "fill automatic property"),
        (CLAGE.ThermalTreatmentProperty, "thermal treatment property"),
        (CLAGE.LeakageDetectionProperty, "leakage detection property"),
        (CLAGE.ValveProperty, "valve property"),
        (CLAGE.RadioModuleProperty, "radio module property"),
        (CLAGE.ScaldingProtectionProperty, "scalding protection property"),
        (CLAGE.TapCountProperty, "tap count property"),
        (CLAGE.DeviceIdentificationProperty, "device identification property"),
        (CLAGE.SoftwareVersionProperty, "software version property"),
        (CLAGE.ArticleNumberProperty, "article number property"),
        (CLAGE.SerialNumberProperty, "serial number property"),
        (CLAGE.ModbusConfigurationProperty, "Modbus configuration property"),
        (CLAGE.ModbusServerAddressProperty, "Modbus server address property"),
        (CLAGE.ModbusWordOrderProperty, "Modbus word order property"),
        (CLAGE.UnsupportedAlternativeProperty, "unsupported alternative property"),
        (CLAGE.CommunicationProtocol, "communication protocol"),
        (CLAGE.ControlClient, "control client"),
        (CLAGE.PowerReductionStrategy, "power reduction strategy"),
        (CLAGE.SpecialValue, "special value"),
        (CLAGE.ObservationProfile, "observation profile"),
        (CLAGE.ActuationProfile, "actuation profile"),
        (CLAGE.QuantityKind, "quantity kind"),
        (CLAGE.ValueRole, "value role"),
        (MODBUS.ModbusSignal, "Modbus signal"),
        (MODBUS.AnalogInputSignal, "analog input signal"),
        (MODBUS.AnalogOutputSignal, "analog output signal"),
        (MODBUS.DigitalInputSignal, "digital input signal"),
        (MODBUS.DigitalOutputSignal, "digital output signal"),
        (MODBUS.InputRegister, "input register"),
        (MODBUS.HoldingRegister, "holding register"),
        (MODBUS.Coil, "coil"),
        (MODBUS.DiscreteInput, "discrete input"),
    ]:
        graph.add((cls, RDF.type, OWL.Class))
        graph.add((cls, RDFS.label, Literal(label, lang="en")))

    for cls in [
        CLAGE.MeasuredValueProperty,
        CLAGE.SetpointProperty,
        CLAGE.LimitProperty,
        CLAGE.ThresholdProperty,
        CLAGE.StatusProperty,
        CLAGE.DiagnosticProperty,
        CLAGE.ControlInputProperty,
        CLAGE.RelativeAdjustmentProperty,
        CLAGE.CounterProperty,
        CLAGE.InstallationConfigurationProperty,
        CLAGE.AvailabilityStatusProperty,
        CLAGE.TemperatureProperty,
        CLAGE.FlowRateProperty,
        CLAGE.FlowVolumeProperty,
        CLAGE.DurationProperty,
        CLAGE.ElectricPowerProperty,
        CLAGE.EnergyProperty,
        CLAGE.OperatingTimeProperty,
        CLAGE.TimerProperty,
        CLAGE.FillAutomaticProperty,
        CLAGE.ThermalTreatmentProperty,
        CLAGE.LeakageDetectionProperty,
        CLAGE.ValveProperty,
        CLAGE.RadioModuleProperty,
        CLAGE.ScaldingProtectionProperty,
        CLAGE.TapCountProperty,
        CLAGE.DeviceIdentificationProperty,
        CLAGE.SoftwareVersionProperty,
        CLAGE.ArticleNumberProperty,
        CLAGE.SerialNumberProperty,
        CLAGE.ModbusConfigurationProperty,
        CLAGE.ModbusServerAddressProperty,
        CLAGE.ModbusWordOrderProperty,
        CLAGE.UnsupportedAlternativeProperty,
    ]:
        graph.add((cls, RDFS.subClassOf, SAREF.Property))

    for cls in [
        MODBUS.AnalogInputSignal,
        MODBUS.AnalogOutputSignal,
        MODBUS.DigitalInputSignal,
        MODBUS.DigitalOutputSignal,
        MODBUS.InputRegister,
        MODBUS.HoldingRegister,
        MODBUS.Coil,
        MODBUS.DiscreteInput,
    ]:
        graph.add((cls, RDFS.subClassOf, MODBUS.ModbusSignal))

    for signal_cls, register_cls in [
        (MODBUS.AnalogInputSignal, MODBUS.InputRegister),
        (MODBUS.AnalogOutputSignal, MODBUS.HoldingRegister),
        (MODBUS.DigitalInputSignal, MODBUS.DiscreteInput),
        (MODBUS.DigitalOutputSignal, MODBUS.Coil),
    ]:
        graph.add((signal_cls, RDFS.subClassOf, register_cls))

    for individual, cls, label in [
        (CLAGE.Electricity, SAREF.Commodity, "electricity"),
        (CLAGE.DomesticHotWater, SAREF.Commodity, "domestic hot water"),
        (CLAGE.ColdWaterInlet, SAREF.FeatureOfInterest, "cold water inlet"),
        (CLAGE.HotWaterOutlet, SAREF.FeatureOfInterest, "hot water outlet"),
        (CLAGE.ControllableValve, SAREF.FeatureOfInterest, "controllable valve"),
        (CLAGE.RadioModule, SAREF.FeatureOfInterest, "radio module"),
        (CLAGE.Bluetooth, CLAGE.CommunicationProtocol, "Bluetooth"),
        (CLAGE.FX3RemoteControl, CLAGE.ControlClient, "CLAGE FX3 remote control"),
        (CLAGE.FXNextRemoteControl, CLAGE.ControlClient, "CLAGE FX Next remote control"),
        (CLAGE.CLAGESmartControlApp, CLAGE.ControlClient, "CLAGE SmartControl app"),
        (CLAGE.Temperature, CLAGE.QuantityKind, "temperature"),
        (CLAGE.TemperatureDifference, CLAGE.QuantityKind, "temperature difference"),
        (CLAGE.FlowRate, CLAGE.QuantityKind, "flow rate"),
        (CLAGE.FlowVolume, CLAGE.QuantityKind, "flow volume"),
        (CLAGE.FillVolume, CLAGE.QuantityKind, "fill volume"),
        (CLAGE.FillDuration, CLAGE.QuantityKind, "fill duration"),
        (CLAGE.FillAutomaticActivation, CLAGE.QuantityKind, "fill automatic activation"),
        (CLAGE.FillByVolumeActive, CLAGE.QuantityKind, "fill by volume active"),
        (CLAGE.FillByTimeActive, CLAGE.QuantityKind, "fill by time active"),
        (CLAGE.TemperatureAdjustment, CLAGE.QuantityKind, "temperature relative adjustment"),
        (CLAGE.FlowRateAdjustment, CLAGE.QuantityKind, "flow-rate relative adjustment"),
        (CLAGE.ElectricPower, CLAGE.QuantityKind, "electric power"),
        (CLAGE.ElectricEnergy, CLAGE.QuantityKind, "electric energy"),
        (CLAGE.PowerUtilization, CLAGE.QuantityKind, "power utilization"),
        (CLAGE.PowerLevelSelection, CLAGE.QuantityKind, "selected power level"),
        (CLAGE.PowerLevelCount, CLAGE.QuantityKind, "power level count"),
        (CLAGE.FlowRateReduction, CLAGE.PowerReductionStrategy, "flow-rate reduction"),
        (
            CLAGE.TemperatureSetpointReduction,
            CLAGE.PowerReductionStrategy,
            "temperature setpoint reduction",
        ),
        (CLAGE.OperatingTime, CLAGE.QuantityKind, "operating time"),
        (CLAGE.OperatingTimeSincePowerOn, CLAGE.QuantityKind, "operating time since power on"),
        (CLAGE.HeatingTime, CLAGE.QuantityKind, "heating time"),
        (CLAGE.SoftwareVersion, CLAGE.QuantityKind, "software version"),
        (CLAGE.ArticleNumber, CLAGE.QuantityKind, "article number"),
        (CLAGE.SerialNumber, CLAGE.QuantityKind, "serial number"),
        (CLAGE.ModbusServerAddress, CLAGE.QuantityKind, "Modbus server address"),
        (CLAGE.BigEndianWordOrder, CLAGE.QuantityKind, "big-endian Modbus word order"),
        (CLAGE.WaterPresenceInDeviceHousing, CLAGE.QuantityKind, "water presence in device housing"),
        (CLAGE.ValvePresence, CLAGE.QuantityKind, "valve presence"),
        (CLAGE.RadioModulePresence, CLAGE.QuantityKind, "radio module presence"),
        (CLAGE.ValveOpening, CLAGE.QuantityKind, "valve opening"),
        (CLAGE.ValveClosedState, CLAGE.QuantityKind, "valve closed state"),
        (CLAGE.TapCount, CLAGE.QuantityKind, "tap count"),
        (CLAGE.ThermalTreatmentActivation, CLAGE.QuantityKind, "thermal treatment activation"),
        (CLAGE.ThermalTreatmentActive, CLAGE.QuantityKind, "thermal treatment active"),
        (CLAGE.ThermalTreatmentInhibited, CLAGE.QuantityKind, "thermal treatment inhibited"),
        (CLAGE.ThermalTreatmentVolume, CLAGE.QuantityKind, "thermal treatment volume"),
        (CLAGE.ThermalTreatmentCount, CLAGE.QuantityKind, "thermal treatment count"),
        (CLAGE.ThermalTreatmentDuration, CLAGE.QuantityKind, "thermal treatment duration"),
        (CLAGE.TimerActivation, CLAGE.QuantityKind, "timer activation"),
        (CLAGE.TimerDuration, CLAGE.QuantityKind, "timer duration"),
        (CLAGE.TimerStopFlowAction, CLAGE.QuantityKind, "timer stop flow action"),
        (CLAGE.TimerStopIfNoFlowCondition, CLAGE.QuantityKind, "timer stop if no flow condition"),
        (CLAGE.TimerNoFlowTimeout, CLAGE.QuantityKind, "timer no-flow timeout"),
        (CLAGE.MeasuredValueRole, CLAGE.ValueRole, "measured value"),
        (CLAGE.SetpointRole, CLAGE.ValueRole, "setpoint"),
        (CLAGE.LimitRole, CLAGE.ValueRole, "limit"),
        (CLAGE.ThresholdRole, CLAGE.ValueRole, "threshold"),
        (CLAGE.StatusRole, CLAGE.ValueRole, "status"),
        (CLAGE.ControlInputRole, CLAGE.ValueRole, "control input"),
        (CLAGE.ActivationRole, CLAGE.ValueRole, "activation"),
        (CLAGE.AdjustmentRole, CLAGE.ValueRole, "relative adjustment"),
        (CLAGE.CounterRole, CLAGE.ValueRole, "counter"),
        (CLAGE.InstallationConfigurationRole, CLAGE.ValueRole, "installation configuration"),
        (CLAGE.AvailabilityRole, CLAGE.ValueRole, "availability"),
        (CLAGE.RemainingValueRole, CLAGE.ValueRole, "remaining value"),
        (CLAGE.TimeoutRole, CLAGE.ValueRole, "timeout"),
        (CLAGE.IdentificationRole, CLAGE.ValueRole, "identification"),
        (CLAGE.ActiveSoftwareVersionRole, CLAGE.ValueRole, "active software version"),
        (CLAGE.InactiveSoftwareVersionRole, CLAGE.ValueRole, "inactive software version"),
        (CLAGE.CurrentRuntimeRole, CLAGE.ValueRole, "current runtime"),
        (CLAGE.CurrentOrLastMeasurementRole, CLAGE.ValueRole, "current or last measurement"),
        (CLAGE.AddressRole, CLAGE.ValueRole, "address"),
        (CLAGE.ConfigurationRole, CLAGE.ValueRole, "configuration"),
        (CLAGE.UnsupportedAlternativeRole, CLAGE.ValueRole, "unsupported alternative"),
    ]:
        graph.add((individual, RDF.type, cls))
        graph.add((individual, RDFS.label, Literal(label, lang="en")))

    graph.add((CLAGE.DomesticHotWater, RDFS.seeAlso, S4WATR.DrinkingWater))
    graph.add((CLAGE.ElectricPower, CLAGE.linearlyProportionalTo, CLAGE.TemperatureDifference))
    graph.add((CLAGE.ElectricPower, CLAGE.linearlyProportionalTo, CLAGE.FlowRate))
    graph.add((CLAGE.ElectricPower, CLAGE.canBeReducedBy, CLAGE.FlowRateReduction))
    graph.add((CLAGE.ElectricPower, CLAGE.canBeReducedBy, CLAGE.TemperatureSetpointReduction))
    graph.add((CLAGE.FlowRateReduction, CLAGE.usesControlProperty, CLAGE.flow_max_lmin10))
    graph.add((CLAGE.FlowRateReduction, CLAGE.reducesProperty, CLAGE.flow_lmin10))
    graph.add((CLAGE.TemperatureSetpointReduction, CLAGE.usesControlProperty, CLAGE.temp_setpoint_C10))
    graph.add((CLAGE.TemperatureSetpointReduction, CLAGE.reducesProperty, CLAGE.temp_setpoint_C10))

    for prop, label in [
        (CLAGE.hasModbusSignal, "has Modbus signal"),
        (CLAGE.modbusSignalType, "Modbus signal type"),
        (CLAGE.modbusSignalAddress, "Modbus signal address"),
        (CLAGE.dataType, "data type"),
        (CLAGE.dataNumberOfBits, "data number of bits"),
        (CLAGE.unitFraction, "unit fraction"),
        (CLAGE.numberOfRegisters, "number of registers"),
        (CLAGE.historicName, "historic name"),
        (CLAGE.functionCode, "function code"),
        (CLAGE.access, "access"),
        (CLAGE.exemplar, "parameter exemplar"),
        (CLAGE.mapsToSarefProperty, "maps to SAREF property"),
        (CLAGE.mapsToSarefExtensionTerm, "maps to SAREF extension term"),
        (CLAGE.describesDevice, "describes device"),
        (CLAGE.hasWaterInlet, "has water inlet"),
        (CLAGE.hasWaterOutlet, "has water outlet"),
        (CLAGE.propertyFeature, "property feature"),
        (CLAGE.affectsProperty, "affects property"),
        (CLAGE.adjustsProperty, "adjusts property"),
        (CLAGE.presenceOf, "presence of"),
        (CLAGE.enablesControlOfProperty, "enables control of property"),
        (CLAGE.enablesLimitationOfProperty, "enables limitation of property"),
        (CLAGE.enablesPowerReductionByProperty, "enables power reduction by property"),
        (CLAGE.enablesCommunicationProtocol, "enables communication protocol"),
        (CLAGE.compatibleControlClient, "compatible control client"),
        (CLAGE.linearlyProportionalTo, "linearly proportional to"),
        (CLAGE.canBeReducedBy, "can be reduced by"),
        (CLAGE.usesControlProperty, "uses control property"),
        (CLAGE.reducesProperty, "reduces property"),
        (CLAGE.identifiesDevice, "identifies device"),
        (CLAGE.hasReadCommand, "has read command"),
        (CLAGE.hasWriteCommand, "has write command"),
        (CLAGE.hasReadOperation, "has read operation"),
        (CLAGE.hasWriteOperation, "has write operation"),
        (CLAGE.hasObservationProfile, "has observation profile"),
        (CLAGE.hasActuationProfile, "has actuation profile"),
        (CLAGE.accessedViaModbusSignal, "accessed via Modbus signal"),
        (CLAGE.currentlySupported, "currently supported"),
        (CLAGE.primaryModbusServerAddress, "primary Modbus server address"),
        (CLAGE.defaultAddressDerivedFrom, "default address derived from"),
        (CLAGE.zeroSerialSuffixDefaultAddress, "default address when serial-number suffix is zero"),
        (CLAGE.appliesToMultipleRegisterValues, "applies to multiple-register values"),
        (CLAGE.maximumProperty, "maximum property"),
        (CLAGE.constrainsProperty, "constrains property"),
        (CLAGE.engineeringUnit, "engineering unit"),
        (CLAGE.scaleFactor, "scale factor from raw value to engineering value"),
        (CLAGE.scaleDivisor, "scale divisor from raw value to engineering value"),
        (CLAGE.quantityKind, "quantity kind"),
        (CLAGE.valueRole, "value role"),
        (CLAGE.minEngineeringValue, "minimum engineering value"),
        (CLAGE.maxEngineeringValue, "maximum engineering value"),
        (CLAGE.minRawValue, "minimum raw value"),
        (CLAGE.maxRawValue, "maximum raw value"),
        (CLAGE.disabledEngineeringValue, "engineering value that disables the heating function"),
        (CLAGE.thermalTreatmentEngineeringValue, "engineering value used during thermal treatment"),
        (CLAGE.disabledRawValue, "raw value that disables the heating function"),
        (CLAGE.thermalTreatmentRawValue, "raw value used during thermal treatment"),
        (CLAGE.equivalentPanelFunction, "equivalent panel function"),
        (CLAGE.positiveDeltaEffect, "positive delta effect"),
        (CLAGE.negativeDeltaEffect, "negative delta effect"),
        (CLAGE.stepEngineeringUnit, "step engineering unit"),
        (CLAGE.coarseStepEngineeringValue, "coarse step engineering value"),
        (CLAGE.fineStepEngineeringValue, "fine step engineering value"),
        (CLAGE.fineStepMinEngineeringValue, "fine-step range minimum engineering value"),
        (CLAGE.fineStepMaxEngineeringValue, "fine-step range maximum engineering value"),
        (CLAGE.coarseStepMinEngineeringValue, "coarse-step range minimum engineering value"),
        (CLAGE.coarseStepMaxEngineeringValue, "coarse-step range maximum engineering value"),
        (CLAGE.hasSpecialValue, "has special value"),
        (CLAGE.rawValue, "raw value"),
        (CLAGE.engineeringValue, "engineering value"),
        (CLAGE.displayLabel, "display label"),
        (CLAGE.valueMeaning, "value meaning"),
        (CLAGE.prioritizesProperty, "prioritizes property"),
        (CLAGE.disablesLimitationOfProperty, "disables limitation of property"),
        (CLAGE.accessesDevice, "accesses device"),
    ]:
        graph.add((prop, RDF.type, RDF.Property))
        graph.add((prop, RDFS.label, Literal(label, lang="en")))


def add_saref_extension_mappings(graph: Graph, subject: URIRef, prop_local: str) -> None:
    if prop_local in SEMANTIC_PROFILES:
        return

    for reference in SAREF_EXTENSION_MAPPINGS.get(prop_local, ()):
        graph.add((subject, CLAGE.mapsToSarefExtensionTerm, reference))
        graph.add((subject, RDFS.seeAlso, reference))
        graph.add((subject, SKOS.closeMatch, reference))

    for property_class in {
        SAREF_EXTENSION_PROPERTY_CLASSES[reference]
        for reference in SAREF_EXTENSION_MAPPINGS.get(prop_local, ())
        if reference in SAREF_EXTENSION_PROPERTY_CLASSES
    }:
        graph.add((subject, RDF.type, property_class))


def add_access_profiles(
    graph: Graph,
    prop_local: str,
    saref_property: URIRef,
    signal: URIRef,
    profile: dict[str, object],
) -> None:
    if profile.get("observed"):
        read_command = clage_resource("command/read", prop_local)
        read_operation = modbus_resource("operation/read", prop_local)
        observation = clage_resource("observation", prop_local)

        graph.add((read_command, RDF.type, SAREF.CommandOfInterest))
        graph.add((read_command, RDFS.label, Literal(f"read {prop_local}", lang="en")))
        graph.add((read_command, SAREF.observes, saref_property))
        graph.add((read_command, CLAGE.accessedViaModbusSignal, signal))

        graph.add((read_operation, RDF.type, SAREF.Operation))
        graph.add((read_operation, RDFS.label, Literal(f"Modbus read {prop_local}", lang="en")))
        graph.add((read_operation, SAREF.represents, read_command))
        graph.add((read_operation, CLAGE.accessedViaModbusSignal, signal))

        graph.add((observation, RDF.type, SAREF.Observation))
        graph.add((observation, RDF.type, CLAGE.ObservationProfile))
        graph.add((observation, RDFS.label, Literal(f"observation profile for {prop_local}", lang="en")))
        graph.add((observation, SAREF.madeBy, DEVICE_INSTANCE))
        graph.add((observation, SAREF.observes, saref_property))
        graph.add((observation, CLAGE.accessedViaModbusSignal, signal))

        graph.add((saref_property, CLAGE.hasReadCommand, read_command))
        graph.add((saref_property, CLAGE.hasReadOperation, read_operation))
        graph.add((saref_property, CLAGE.hasObservationProfile, observation))

    if profile.get("controlled"):
        write_command = clage_resource("command/write", prop_local)
        write_operation = modbus_resource("operation/write", prop_local)
        actuation = clage_resource("actuation", prop_local)

        graph.add((write_command, RDF.type, SAREF.CommandOfInterest))
        graph.add((write_command, RDFS.label, Literal(f"write {prop_local}", lang="en")))
        graph.add((write_command, SAREF.controls, saref_property))
        graph.add((write_command, SAREF.hasInput, saref_property))
        graph.add((write_command, CLAGE.accessedViaModbusSignal, signal))

        graph.add((write_operation, RDF.type, SAREF.Operation))
        graph.add((write_operation, RDFS.label, Literal(f"Modbus write {prop_local}", lang="en")))
        graph.add((write_operation, SAREF.represents, write_command))
        graph.add((write_operation, CLAGE.accessedViaModbusSignal, signal))

        graph.add((actuation, RDF.type, SAREF.Actuation))
        graph.add((actuation, RDF.type, CLAGE.ActuationProfile))
        graph.add((actuation, RDFS.label, Literal(f"actuation profile for {prop_local}", lang="en")))
        graph.add((actuation, SAREF.madeBy, DEVICE_INSTANCE))
        graph.add((actuation, SAREF.controls, saref_property))
        graph.add((actuation, SAREF.hasInput, saref_property))
        graph.add((actuation, CLAGE.accessedViaModbusSignal, signal))

        graph.add((saref_property, CLAGE.hasWriteCommand, write_command))
        graph.add((saref_property, CLAGE.hasWriteOperation, write_operation))
        graph.add((saref_property, CLAGE.hasActuationProfile, actuation))


def add_row(graph: Graph, row: dict[str, str]) -> None:
    prop_local = property_name(row)
    saref_property = CLAGE[prop_local]
    signal = MODBUS[f"signal/{prop_local}"]
    unit_fraction = row["unit fraction"].strip()
    historic_name = row["historic name"].strip()
    signal_type = row["modbus signal type"].strip()
    datatype = row["data type"].strip()

    graph.add((saref_property, RDF.type, SAREF.Property))
    graph.add((saref_property, RDFS.label, Literal(row["Parameter name"].strip(), lang="en")))
    add_literal(graph, saref_property, RDFS.comment, row["comment"])
    add_saref_extension_mappings(graph, saref_property, prop_local)

    if unit_fraction != "none":
        unit = UNIT[local_name(unit_fraction)]
        graph.add((unit, RDF.type, SAREF.UnitOfMeasure))
        graph.add(
            (
                unit,
                RDFS.label,
                Literal(UNIT_LABELS.get(unit_fraction, unit_fraction), lang="en"),
            )
        )
        graph.add((saref_property, SAREF.isMeasuredIn, unit))
        graph.add((saref_property, CLAGE.unitFraction, Literal(unit_fraction)))

        if unit_fraction in UNIT_SEMANTICS:
            semantics = UNIT_SEMANTICS[unit_fraction]
            graph.add(
                (
                    unit,
                    CLAGE.engineeringUnit,
                    Literal(semantics["engineering_unit"], lang="en"),
                )
            )
            graph.add(
                (
                    saref_property,
                    CLAGE.engineeringUnit,
                    Literal(semantics["engineering_unit"], lang="en"),
                )
            )
            graph.add(
                (
                    saref_property,
                    CLAGE.scaleFactor,
                    Literal(semantics["scale_factor"], datatype=XSD.decimal),
                )
            )
            graph.add(
                (
                    saref_property,
                    CLAGE.scaleDivisor,
                    Literal(semantics["scale_divisor"], datatype=XSD.decimal),
                )
            )

    if prop_local in SEMANTIC_PROFILES:
        profile = SEMANTIC_PROFILES[prop_local]
        for cls in profile.get("classes", ()):
            graph.add((saref_property, RDF.type, cls))
        graph.add((saref_property, CLAGE.valueRole, profile["role"]))
        graph.add((saref_property, CLAGE.quantityKind, profile["quantity_kind"]))
        if "property_kind" in profile:
            property_kind = profile["property_kind"]
            graph.add((saref_property, SKOS.broader, property_kind))
            graph.add((saref_property, RDFS.seeAlso, property_kind))
            graph.add((saref_property, CLAGE.mapsToSarefExtensionTerm, property_kind))
            if property_kind in SAREF_EXTENSION_PROPERTY_CLASSES:
                graph.add((saref_property, RDF.type, SAREF_EXTENSION_PROPERTY_CLASSES[property_kind]))
        for extension_term in profile.get("extension_terms", ()):
            graph.add((saref_property, RDFS.seeAlso, extension_term))
            graph.add((saref_property, CLAGE.mapsToSarefExtensionTerm, extension_term))
        if "affects_property" in profile:
            graph.add((saref_property, CLAGE.affectsProperty, profile["affects_property"]))
        if "adjusts_property" in profile:
            graph.add((saref_property, CLAGE.adjustsProperty, profile["adjusts_property"]))
        if "presence_of" in profile:
            graph.add((saref_property, CLAGE.presenceOf, profile["presence_of"]))
        for controlled_property in profile.get("enables_control_of_properties", ()):
            graph.add((saref_property, CLAGE.enablesControlOfProperty, controlled_property))
        for limited_property in profile.get("enables_limitation_of_properties", ()):
            graph.add((saref_property, CLAGE.enablesLimitationOfProperty, limited_property))
        for reduction_property in profile.get("enables_power_reduction_by_properties", ()):
            graph.add((saref_property, CLAGE.enablesPowerReductionByProperty, reduction_property))
        if "enables_communication_protocol" in profile:
            graph.add(
                (
                    saref_property,
                    CLAGE.enablesCommunicationProtocol,
                    profile["enables_communication_protocol"],
                )
            )
        for control_client in profile.get("compatible_control_clients", ()):
            graph.add((saref_property, CLAGE.compatibleControlClient, control_client))
        if "feature" in profile:
            graph.add((saref_property, CLAGE.propertyFeature, profile["feature"]))
        if "maximum_property" in profile:
            graph.add((saref_property, CLAGE.maximumProperty, profile["maximum_property"]))
        if "constrains_property" in profile:
            graph.add((saref_property, CLAGE.constrainsProperty, profile["constrains_property"]))
        if profile.get("identifies_device"):
            graph.add((saref_property, CLAGE.identifiesDevice, DEVICE_INSTANCE))
        if "currently_supported" in profile:
            graph.add(
                (
                    saref_property,
                    CLAGE.currentlySupported,
                    Literal(profile["currently_supported"], datatype=XSD.boolean),
                )
            )
        if "primary_modbus_server_address" in profile:
            graph.add(
                (
                    saref_property,
                    CLAGE.primaryModbusServerAddress,
                    Literal(profile["primary_modbus_server_address"], datatype=XSD.boolean),
                )
            )
        if "default_address_derived_from" in profile:
            graph.add(
                (
                    saref_property,
                    CLAGE.defaultAddressDerivedFrom,
                    profile["default_address_derived_from"],
                )
            )
        if "zero_serial_suffix_default_address" in profile:
            graph.add(
                (
                    saref_property,
                    CLAGE.zeroSerialSuffixDefaultAddress,
                    Literal(profile["zero_serial_suffix_default_address"], datatype=XSD.integer),
                )
            )
        if "applies_to_multiple_register_values" in profile:
            graph.add(
                (
                    saref_property,
                    CLAGE.appliesToMultipleRegisterValues,
                    Literal(profile["applies_to_multiple_register_values"], datatype=XSD.boolean),
                )
            )
        if profile.get("observed"):
            graph.add((DEVICE_INSTANCE, SAREF.observes, saref_property))
        if profile.get("controlled"):
            graph.add((DEVICE_INSTANCE, SAREF.controls, saref_property))

        min_value = profile.get("min_engineering_value")
        max_value = profile.get("max_engineering_value")
        min_raw_value = profile.get("min_raw_value")
        max_raw_value = profile.get("max_raw_value")
        disabled_value = profile.get("disabled_engineering_value")
        thermal_treatment_value = profile.get("thermal_treatment_engineering_value")
        equivalent_panel_function = profile.get("equivalent_panel_function")
        positive_delta_effect = profile.get("positive_delta_effect")
        negative_delta_effect = profile.get("negative_delta_effect")
        step_engineering_unit = profile.get("step_engineering_unit")
        if min_value is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.minEngineeringValue,
                    Literal(min_value, datatype=XSD.decimal),
                )
            )
        if max_value is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.maxEngineeringValue,
                    Literal(max_value, datatype=XSD.decimal),
                )
            )
        if disabled_value is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.disabledEngineeringValue,
                    Literal(disabled_value, datatype=XSD.decimal),
                )
            )
        if thermal_treatment_value is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.thermalTreatmentEngineeringValue,
                    Literal(thermal_treatment_value, datatype=XSD.decimal),
                )
            )
        if equivalent_panel_function is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.equivalentPanelFunction,
                    Literal(equivalent_panel_function, lang="en"),
                )
            )
        if positive_delta_effect is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.positiveDeltaEffect,
                    Literal(positive_delta_effect, lang="en"),
                )
            )
        if negative_delta_effect is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.negativeDeltaEffect,
                    Literal(negative_delta_effect, lang="en"),
                )
            )
        if step_engineering_unit is not None:
            graph.add(
                (
                    saref_property,
                    CLAGE.stepEngineeringUnit,
                    Literal(step_engineering_unit, lang="en"),
                )
            )
        for key, predicate in [
            ("coarse_step_engineering_value", CLAGE.coarseStepEngineeringValue),
            ("fine_step_engineering_value", CLAGE.fineStepEngineeringValue),
            ("fine_step_min_engineering_value", CLAGE.fineStepMinEngineeringValue),
            ("fine_step_max_engineering_value", CLAGE.fineStepMaxEngineeringValue),
            ("coarse_step_min_engineering_value", CLAGE.coarseStepMinEngineeringValue),
            ("coarse_step_max_engineering_value", CLAGE.coarseStepMaxEngineeringValue),
        ]:
            value = profile.get(key)
            if value is not None:
                graph.add((saref_property, predicate, Literal(value, datatype=XSD.decimal)))
        for special_value in profile.get("special_values", ()):
            special_resource = special_value["resource"]
            graph.add((special_resource, RDF.type, CLAGE.SpecialValue))
            graph.add((saref_property, CLAGE.hasSpecialValue, special_resource))
            if "raw_value" in special_value:
                graph.add(
                    (
                        special_resource,
                        CLAGE.rawValue,
                        raw_value_literal(special_value["raw_value"]),
                    )
                )
            if "engineering_value" in special_value:
                graph.add(
                    (
                        special_resource,
                        CLAGE.engineeringValue,
                        Literal(special_value["engineering_value"], datatype=XSD.decimal),
                    )
                )
            if "display_label" in special_value:
                graph.add(
                    (
                        special_resource,
                        CLAGE.displayLabel,
                        Literal(special_value["display_label"], lang="en"),
                    )
                )
            if "meaning" in special_value:
                graph.add(
                    (
                        special_resource,
                        CLAGE.valueMeaning,
                        Literal(special_value["meaning"], lang="en"),
                    )
                )
            if "prioritizes_property" in special_value:
                graph.add(
                    (
                        special_resource,
                        CLAGE.prioritizesProperty,
                        special_value["prioritizes_property"],
                    )
                )
            if "disables_limitation_of_property" in special_value:
                graph.add(
                    (
                        special_resource,
                        CLAGE.disablesLimitationOfProperty,
                        special_value["disables_limitation_of_property"],
                    )
                )
        if unit_fraction in UNIT_SEMANTICS:
            scale_factor = UNIT_SEMANTICS[unit_fraction]["scale_factor"]
            if min_value is not None:
                graph.add(
                    (
                        saref_property,
                        CLAGE.minRawValue,
                        raw_value_literal(
                            min_raw_value if min_raw_value is not None else min_value / scale_factor,
                        ),
                    )
                )
            if max_value is not None:
                graph.add(
                    (
                        saref_property,
                        CLAGE.maxRawValue,
                        raw_value_literal(
                            max_raw_value if max_raw_value is not None else max_value / scale_factor,
                        ),
                    )
                )
            if disabled_value is not None:
                graph.add(
                    (
                        saref_property,
                        CLAGE.disabledRawValue,
                        Literal(disabled_value / scale_factor, datatype=XSD.decimal),
                    )
                )
            if thermal_treatment_value is not None:
                graph.add(
                    (
                        saref_property,
                        CLAGE.thermalTreatmentRawValue,
                        Literal(thermal_treatment_value / scale_factor, datatype=XSD.decimal),
                    )
                )

    graph.add((DEVICE_INSTANCE, SAREF.hasProperty, saref_property))
    graph.add((REGISTER_MAP, CLAGE.hasModbusSignal, signal))

    graph.add((signal, RDF.type, MODBUS.ModbusSignal))
    if signal_type in SIGNAL_CLASS:
        graph.add((signal, RDF.type, SIGNAL_CLASS[signal_type]))
    if historic_name in REGISTER_CLASS:
        graph.add((signal, RDF.type, REGISTER_CLASS[historic_name]))

    graph.add((signal, CLAGE.mapsToSarefProperty, saref_property))
    graph.add((signal, CLAGE.accessesDevice, DEVICE_INSTANCE))
    graph.add((signal, CLAGE.modbusSignalType, Literal(signal_type)))
    graph.add((signal, CLAGE.modbusSignalAddress, Literal(row["modbus signal ID"], datatype=XSD.integer)))
    graph.add((signal, CLAGE.dataType, Literal(datatype)))
    graph.add((signal, CLAGE.dataNumberOfBits, Literal(row["data number of bits"], datatype=XSD.integer)))
    graph.add((signal, CLAGE.numberOfRegisters, Literal(row["number of registers"], datatype=XSD.integer)))
    graph.add((signal, CLAGE.historicName, Literal(historic_name)))
    graph.add((signal, CLAGE.access, Literal(row["access"].strip())))
    graph.add((signal, CLAGE.exemplar, Literal(row["Parameter exemplar"].strip(), datatype=XSD.integer)))
    add_literal(graph, signal, RDFS.comment, row["comment"])

    if datatype in DATA_TYPES:
        graph.add((signal, CLAGE.valueDatatype, DATA_TYPES[datatype]))

    for code in row["function codes used"].split():
        graph.add((signal, CLAGE.functionCode, Literal(code)))

    if prop_local in SEMANTIC_PROFILES:
        add_access_profiles(graph, prop_local, saref_property, signal, SEMANTIC_PROFILES[prop_local])


def build_graph() -> Graph:
    graph = Graph()
    graph.bind("clage", CLAGE)
    graph.bind("device", DEVICE)
    graph.bind("modbus", MODBUS)
    graph.bind("saref", SAREF)
    graph.bind("s4ener", S4ENER)
    graph.bind("s4syst", S4SYST)
    graph.bind("s4watr", S4WATR)
    graph.bind("unit", UNIT)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)

    add_schema(graph)
    with CSV_FILE.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            add_row(graph, row)
    return graph


def main() -> None:
    graph = build_graph()
    graph.serialize(destination=TTL_FILE, format="turtle")
    print(f"wrote {TTL_FILE} with {len(graph)} triples")


if __name__ == "__main__":
    main()

# EOF
