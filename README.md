<p align="center"><img src="https://www.clage.com/assets/gfx/logo.svg" alt="CLAGE GmbH" width="150"> <i>Modbus</i></p>

# CLAGE GmbH Modbus API

* [**Mapping Table**](src/clage_modbus_mapping.csv)
* [Modbus **Wiki**](../../wiki)
  * [Python Modbus **Tool/Module**](../../wiki/clage_modbus.py)

Automatically translated versions <span class="notranslate" translate="no">[**DE**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=de&_x_tr_hl=de-DE&_x_tr_pto=wapp), [**FR**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=fr&_x_tr_hl=fr-FR&_x_tr_pto=wapp), [**NL**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=nl&_x_tr_hl=nl-NL&_x_tr_pto=wapp), [**PL**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=pl&_x_tr_hl=pl-PL&_x_tr_pto=wapp), [**PT**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=pt&_x_tr_hl=pt-PT&_x_tr_pto=wapp), [**ES**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=es&_x_tr_hl=es-ES&_x_tr_pto=wapp), [**RU**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=ru&_x_tr_hl=ru-RU&_x_tr_pto=wapp), [**CS**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=cs&_x_tr_hl=cs-CS&_x_tr_pto=wapp), [**SK**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=sk&_x_tr_hl=sk-SK&_x_tr_pto=wapp), [**BG**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=bg&_x_tr_hl=bg-BG&_x_tr_pto=wapp), [**SR**](https://github-com.translate.goog/clage-gmbh/clage_modbus?_x_tr_sl=auto&_x_tr_tl=sr&_x_tr_hl=sr-SR&_x_tr_pto=wapp)</span> *Do not click twice. There is not translation of the translation.*

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
