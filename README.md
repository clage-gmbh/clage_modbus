# CLAGE GmbH devices Modbus API

## Hardware

At the [ISH 2023 CLAGE announced](https://www.haustechnikdialog.de/News/27889/Neue-E-Durchlauferhitzer-auf-der-ISH-2023) a new device called **ISX** providing [REST API](https://github.com/clage-gmbh/rest_api) by WLAN and Modbus RTU by wire.

## Documentation

The REST API documentation can be found in a [clage-gmbh/rest_api](https://github.com/clage-gmbh/rest_api).

For using the Modbus RTU interface there is an open source [command line tool written in Python](clage_modbus/clage_modbus.py) to demonstrate the usage.
The mapping of the device parameters to the Modbus register addresses is provided as a

* [CSV table](clage_modbus/clage_modbus_mapping.csv) and a
* [Python map](clage_modbus/clage_modbus_mapping.py)

The command line tools can be loaded as a module providing a Python class to set and access parameters of a CLAGE device.

## Topology

Like any other Modbus RTU device, a water heater can be connected to a Modbus RTU to TCP gateway.
This allows the control of several devices on the RTU bus via a single gateway from within a LAN (see [clage_modbus.py](clage_modbus/`clage_modbus.py`) option `-i`  or `--ip_addr`).

This allows the advantages of both concepts to be used:

* A single YCYM 2x2x0,8 or J-Y(St) Y 2x2x0,8 wire can be installed as a [bus network](https://en.wikipedia.org/wiki/Bus_network) to connect several devices. According to DIN VDE 0829 Teil 522 bzw. DIN EN 50090-5-2, this cable may be routed directly together with the power supply cable.
* Such buses can be connected at any point to a LAN using a single gateway per bus (not per device).

With this concept one can connect plenty devices distributed over a huge building with a minimum installation effort.
No [star network](https://en.wikipedia.org/wiki/Star_network) or separated wire channels are needed.
Reliable, interference-free wired networking with optimum economy.

> **Hint**: Behind the RTU/TCP modbus gateway the water heating devices can be controlled by [**Modbus TCP**](https://en.wikipedia.org/wiki/Modbus#Modbus_TCP_frame_format) only. There is no REST API as provided over WLAN and thus the smartphone APP will not work with that.

## License

Copyright 2023 CLAGE GmbH, Germany

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
      <http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

All code here is provided under the [Apache License 2.0](https://fossa.com/blog/open-source-licenses-101-apache-license-2-0/) or above.
