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

"""LINCOT Constants."""

__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright 2023 Sensors & Signals LLC"
__license__ = "Apache License, Version 2.0"

# Default CoT stale period (in seconds).
DEFAULT_COT_STALE: str = "3600"  # 1 hour

# Default CoT event type ("marker type").
DEFAULT_COT_TYPE: str = "a-f-G-E-S"

# Default poll interval (in seconds) for GPS Info data.
DEFAULT_POLL_INTERVAL: int = 61

# Default command to retrieve GPS Info data.
DEFAULT_GPS_INFO_CMD: str = "gpspipe -w -n 5"
