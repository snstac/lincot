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

"""Position source helpers for LINCOT."""

from configparser import SectionProxy
from typing import Optional, Union


def static_position_configured(config: Union[dict, SectionProxy, None]) -> bool:
    """Return True when STATIC_LAT and STATIC_LON are both set."""
    config = config or {}
    lat = config.get("STATIC_LAT")
    lon = config.get("STATIC_LON")
    return bool(
        lat is not None
        and lon is not None
        and str(lat).strip()
        and str(lon).strip()
    )


def static_tpv(config: Union[dict, SectionProxy, None]) -> Optional[dict]:
    """Build a gpspipe-compatible TPV dict from static coordinates."""
    if not static_position_configured(config):
        return None
    config = config or {}
    return {
        "class": "TPV",
        "lat": float(config.get("STATIC_LAT")),
        "lon": float(config.get("STATIC_LON")),
        "altHAE": config.get("STATIC_HAE") or "9999999.0",
        "track": config.get("STATIC_COURSE") or "0.0",
        "speed": config.get("STATIC_SPEED") or "0.0",
    }
