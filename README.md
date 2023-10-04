<p align="center"><img src="https://www.clage.com/assets/gfx/logo.svg" alt="CLAGE GmbH" width="150"> <i>Modbus</i></p>

# CLAGE GmbH Modbus API

* [**Mapping Table**](../blob/main/src/clage_modbus_mapping.csv)
* [Modbus **Wiki**](../../wiki)
  * [Python Modbus **Tool/Module**](../../wiki/clage_modbus.py)

## Hardware

As part of the [ISH 2023, CLAGE announced](https://www.haustechnikdialog.de/News/27889/Neue-E-Durchlauferhitzer-auf-der-ISH-2023) a new device called **ISX** providing [**REST API**](https://github.com/clage-gmbh/rest_api) by WLAN and **Modbus RTU** by wire.

* [ISX in CLAGE Product Guide](https://www.clage.com/de/Mediacenter/b432f34c5a997c8e7c806a895ecc5e25/CLAGE-Produkt-Guide-de.pdf) *page 4 upper left*

## Documentation

* REST API documentation can be found in [clage-gmbh/rest_api](https://github.com/clage-gmbh/rest_api).
* Modbus API documentation can be found in [this GitHub Wiki](../../wiki).

The mapping of the device parameters to the modbus register addresses is provided as a [CSV table](src/clage_modbus_mapping.csv) and a [Python map](src/clage_modbus_mapping.py).

For using the Modbus RTU interface there is an open source [command line tool written in Python](src/clage_modbus.py) to test and demonstrate the usage.
The command line tools can also be loaded as a module providing a Python class to access parameters of a CLAGE device.

## License

Copyright 2023 CLAGE GmbH, Germany

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

All code here is provided under the [Apache License 2.0](https://fossa.com/blog/open-source-licenses-101-apache-license-2-0/) or above.
