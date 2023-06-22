#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Sensors & Signals LLC
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

"""LINCOT: Linux GPS to TAK Gateway.

:source: <https://github.com/snstac/lincot>
"""

from .constants import (
    DEFAULT_COT_TYPE,
    DEFAULT_COT_STALE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_GPS_INFO_CMD,
)

from .functions import gpspipe_to_cot, create_tasks  # NOQA

from .classes import LincotWorker  # NOQA

__version__ = "1.0.2-beta2"
__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright 2023 Sensors & Signals LLC"
__license__ = "Apache License, Version 2.0"
