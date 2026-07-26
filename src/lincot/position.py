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

import json
from configparser import SectionProxy
from typing import Any, Dict, Iterable, Optional, Union

# Satellite/DOP fields worth lifting out of the gpsd SKY report.
SKY_FIELDS = ("hdop", "pdop", "vdop", "gdop", "nSat", "uSat")


def merge_sky(gps_info: Dict[str, Any], sky_lines: Iterable[str]) -> Dict[str, Any]:
    """Merge satellite/DOP quality from gpsd SKY reports into a TPV dict.

    gpsd emits SKY in two flavors: a full sky view carrying ``satellites`` (and
    ``uSat``/``nSat``), and DOP-only updates in between — on a u-blox 7 only
    every third SKY is the full one. Taking just the last SKY in a sample
    therefore loses the satellite counts most of the time, which is exactly what
    happened in the field (HDOP present, sats missing). So scan every SKY and
    keep the last non-null value per field, and fall back to counting the
    ``satellites`` array when the explicit counts are absent.
    """
    for line in sky_lines or []:
        try:
            sky = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue

        for key in SKY_FIELDS:
            val = sky.get(key)
            if val is not None:
                gps_info[key] = val

        sats = sky.get("satellites")
        if isinstance(sats, list) and sats:
            gps_info.setdefault("nSat", len(sats))
            if gps_info.get("uSat") is None:
                gps_info["uSat"] = sum(1 for s in sats if s.get("used"))
    return gps_info


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
