LINCOT - Linux GPS to TAK Gateway
*********************************


Installation
============

**LINCOT requires Python 3.6 or above.**

LINCOT functionality is provided by a command-line tool called ``lincot``, which can be 
installed several ways.

Installing as a Debian/Ubuntu Package [Use Me!]::

    $ wget https://github.com/ampledata/pytak/releases/latest/download/python3-pytak_latest_all.deb
    $ sudo apt install -f ./python3-pytak_latest_all.deb
    $ wget https://github.com/ampledata/lincot/releases/latest/download/python3-lincot_latest_all.deb
    $ sudo apt install -f ./python3-lincot_latest_all.deb

Install from the Python Package Index [Alternative]::

    $ python3 -m pip install -U pytak
    $ python3 -m pip install -U lincot

Install from this source tree [Developer]::

    $ git clone https://github.com/ampledata/lincot.git
    $ cd lincot/
    $ python3 -m pip install .


Usage
=====

LINCOT can be configured with a INI-style configuration file, or using 
environmental variables.

Command-line options::

    usage: lincot [-h] [-c CONFIG_FILE] [-p PREF_PACKAGE]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG_FILE, --CONFIG_FILE CONFIG_FILE
                            Optional configuration file. Default: config.ini
    -p PREF_PACKAGE, --PREF_PACKAGE PREF_PACKAGE
                            Optional connection preferences package zip file (aka Data Package).

Configuration options:
    ``COT_URL`` : str,  default: udp://239.2.3.1:6969
        URL to CoT destination. Must be a URL, e.g. ``tcp://1.2.3.4:1234`` or ``tls://...:1234``, etc. See `PyTAK <https://github.com/ampledata/pytak#configuration-parameters>`_ for options, including TLS support.
    ``COT_STALE`` : int, default: 3600
        CoT Stale period ("timeout"), in seconds. Default `3600` seconds (1 hour).
    ``COT_TYPE`` : str, default: a-u-S-X-M
        Override COT Event Type ("marker type").

See example-config.ini in the source tree for example configuration.


# python3 -c "import uuid;nn=str(uuid.getnode());print(nn[len(nn)-4:len(nn)])"

Source
======
Github: https://github.com/snstac/lincot


License & Copyright
===================

Copyright 2023 Sensors & Signals LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
