# SAREF RDF/OWL for CLAGE Modbus/RTU

Python script for creating an OWL Turtle file from the table of parameters available via Modbus/RTU.
This file defines a semantic mapping from the [proprietary CLAGE Modbus API](https://github.com/clage-gmbh/clage_modbus) to [SAREF](https://saref.etsi.org) using the API syntax as defined in [`clage_modbus_tab.csv`](../clage_modbus_tab.csv).

## `build.sh`

This Bash script simplifies the creation of derived files.
Run `./build.sh -?` to see the available options.

## `protege`

This is a Bash script that can be copied to your personal `~/bin/` directory so that `protege` in `/opt/protege/Protege-5.6.9/` can be started from anywhere as a normal command without specifying the full path.

## `clage_modbus_ttl.py`

Script for converting the Modbus table `clage_modbus_tab.csv` into an OWL Turtle file describing RDF data.

## SAREF Extensions

In a **building**, an **instantaneous water heater** is an actuator in the **water infrastructure** that uses electrical **energy** to heat the water flowing through it.
In addition to the SAREF core

* [SAREF](https://saref.etsi.org)

the following extensions are therefore relevant:

* [SAREF4ENER](https://saref.etsi.org/saref4ener) Energy
* [SAREF4BLDG](https://saref.etsi.org/saref4bldg) Building
* [SAREF4WATR](https://saref.etsi.org/saref4watr) Water

## `ttl_to_svg.py`

This Python script rather mechanically creates a vector SVG graphic from the relationships in the Turtle file.
It is included here only for completeness and is usually not very helpful for non-trivial projects, because the resulting SVG graphic becomes very large and hard to read.

## `sparql_example_*.py`

These scripts demonstrate queries against the information stored in the Turtle file using the **SPARQL Protocol and RDF Query Language** in Python.
This works somewhat like the *Structured Query Language* (SQL) used for databases, but on semantic RDF/OWL data.

This is where the actual benefit of this approach becomes visible.
A large system, for example for building automation, is not interested in the individual parameters of the actuators and sensors in the building, and certainly not in the exact way each manufacturer named them.
Such information would create a harmful web of dependencies.
SAREF and its extensions therefore provide a semantic framework in which devices from different manufacturers can position themselves.

In a specific case, building automation knows a task, for example that it should set a temperature setpoint, turns that into a SAREF query, and then learns the details of how this temperature can be set and within which limits.
This example is e.g. demonstrated in [`sparql_example_03.py`](./sparql_example_03.py).

In this way, devices can be integrated into building automation without explicitly configuring addresses, IDs, and interfaces.
The device itself provides the mapping of its control variables into a higher-level semantic context as a SAREF RDF/OWL model.

Devices can therefore fulfill roles and their tasks without the central control system having to be configured with the exact implementation details of how each device is controlled.
Rule sets such as EEBUS CoC 1.0 then define the minimum set of tasks or use cases that must be represented.
They therefore define the minimum set of capabilities a device must provide.
Instantaneous water heaters are currently not covered by EEBUS CoC 1.0.
This ontology is therefore built by trying to cover as much as possible with limited effort.
