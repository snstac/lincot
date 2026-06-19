#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""LINCOT Constants."""

import socket

_hostname = socket.gethostname()

DEFAULT_COT_STALE: str = "3600"
DEFAULT_COT_TYPE: str = "a-f-G-E-S"
DEFAULT_POLL_INTERVAL: int = 61
DEFAULT_GPS_INFO_CMD: str = "gpspipe --json -n 5"
DEFAULT_SSH_USER: str = "pi"
DEFAULT_COCKPIT_PORT: int = 9090
DEFAULT_REMARKS_EXTRA_CMD_TIMEOUT: float = 2.0
DEFAULT_COT_DETAIL_XML_CMD_TIMEOUT: float = 2.0
MACHINE_ID_PATHS = ("/etc/machine-id", "/var/lib/dbus/machine-id")

# Sensor keep-alive / heartbeat
DEFAULT_SENSOR_KEEPALIVE_PERIOD: int = 30
DEFAULT_SENSOR_LAT: float = 0.0
DEFAULT_SENSOR_LON: float = 0.0
DEFAULT_SENSOR_HAE: float = 0.0
DEFAULT_SENSOR_ID: str = f"lincot_{_hostname}"
DEFAULT_SENSOR_COT_TYPE: str = "a-f-G-E-S-E"
DEFAULT_SENSOR_PAYLOAD_TYPE: str = "GPS-Receiver"
