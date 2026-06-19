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

"""LINCOT: Linux GPS to TAK Gateway."""

from pathlib import Path

__version__ = (
    Path(__file__).resolve().parent.joinpath("VERSION").read_text(encoding="utf-8").strip()
)

from lincot.constants import (  # noqa: E402
    DEFAULT_COCKPIT_PORT,
    DEFAULT_COT_DETAIL_XML_CMD_TIMEOUT,
    DEFAULT_COT_STALE,
    DEFAULT_COT_TYPE,
    DEFAULT_GPS_INFO_CMD,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_REMARKS_EXTRA_CMD_TIMEOUT,
    DEFAULT_SSH_USER,
    DEFAULT_SENSOR_COT_TYPE,
    DEFAULT_SENSOR_HAE,
    DEFAULT_SENSOR_ID,
    DEFAULT_SENSOR_KEEPALIVE_PERIOD,
    DEFAULT_SENSOR_LAT,
    DEFAULT_SENSOR_LON,
    DEFAULT_SENSOR_PAYLOAD_TYPE,
    MACHINE_ID_PATHS,
)
from lincot.functions import (  # noqa: E402
    create_tasks,
    gen_sensor_cot,
    gpspipe_to_cot,
    gpspipe_to_cot_xml,
    position_to_cot,
    position_to_cot_xml,
)
from lincot.classes import LincotWorker, SensorWorker  # noqa: E402
