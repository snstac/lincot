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

"""LINCOT functions for parsing position data and generating Cursor on Target."""

from configparser import SectionProxy
import math
import shlex
import subprocess
from typing import Optional, Union
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

import pytak

import lincot
from lincot.identity import get_callsign, get_uid
from lincot.position import static_position_configured
from lincot.remarks import build_remarks, get_cockpit_url


def _detail_children_from_command(
    config: Union[dict, SectionProxy, None],
) -> list[Element]:
    """Run an optional command that emits XML detail children."""
    config = config or {}
    command = str(config.get("COT_DETAIL_XML_CMD") or "").strip()
    if not command:
        return []
    try:
        timeout = float(
            config.get("COT_DETAIL_XML_CMD_TIMEOUT")
            or lincot.DEFAULT_COT_DETAIL_XML_CMD_TIMEOUT
        )
    except (TypeError, ValueError):
        timeout = lincot.DEFAULT_COT_DETAIL_XML_CMD_TIMEOUT
    try:
        run = subprocess.run(
            shlex.split(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    if run.returncode != 0:
        return []
    xml_text = (run.stdout or "").strip()
    if not xml_text:
        return []
    try:
        wrapper = ET.fromstring(f"<detail-fragment>{xml_text}</detail-fragment>")
    except ET.ParseError:
        return []
    return list(wrapper)


def create_tasks(config: Union[dict, SectionProxy], clitool: pytak.CLITool) -> set:
    """Bootstrap coroutine tasks for this PyTAK application."""
    tasks = {lincot.LincotWorker(clitool.tx_queue, config)}
    tasks.add(lincot.SensorWorker(clitool.tx_queue, config))
    return tasks


def _position_source(config: Union[dict, SectionProxy, None]) -> str:
    if static_position_configured(config):
        return "static"
    return "gpsd"


def _horizontal_error(gps_info: dict) -> str:
    """Return CoT circular error from gpsd TPV accuracy fields."""
    if gps_info.get("eph") is not None:
        return str(gps_info.get("eph"))
    try:
        return str(math.hypot(float(gps_info["epx"]), float(gps_info["epy"])))
    except (KeyError, TypeError, ValueError):
        return "9999999.0"


def _vertical_error(gps_info: dict) -> str:
    """Return CoT linear error from gpsd TPV vertical accuracy."""
    if gps_info.get("epv") is not None:
        return str(gps_info.get("epv"))
    return "9999999.0"


# pylint: disable=too-many-locals
def position_to_cot_xml(
    gps_info: dict,
    config: Union[dict, SectionProxy, None] = None,
) -> Optional[Element]:
    """Convert a TPV position dict to a Cursor on Target event."""
    config = config or {}

    if gps_info.get("class") != "TPV":
        return None

    lat = gps_info.get("lat")
    lon = gps_info.get("lon")
    if lat is None or lon is None:
        return None

    cot_type: str = str(config.get("COT_TYPE") or lincot.DEFAULT_COT_TYPE)
    cot_stale: int = int(config.get("COT_STALE") or lincot.DEFAULT_COT_STALE)
    cot_callsign: str = get_callsign(config)
    uid: str = get_uid(config)
    position_source = _position_source(config)
    cockpit_url = get_cockpit_url(config)

    point = pytak.cot_point(
        lat=lat,
        lon=lon,
        hae=gps_info.get("altHAE") or gps_info.get("altMSL") or "9999999.0",
        ce=_horizontal_error(gps_info),
        le=_vertical_error(gps_info),
    )

    track = Element("track")
    track.set("course", str(gps_info.get("track") or "0.0"))
    track.set("speed", str(gps_info.get("speed") or "0.0"))

    contact = Element("contact")
    contact.set("callsign", cot_callsign)

    link = Element("link")
    link.set("url", cockpit_url.rstrip("/"))
    link.set("relation", "r-u")
    link.set("type", cot_type)

    detail = pytak.cot_detail(track, contact)
    pytak.add_remarks(detail, [build_remarks(config, position_source=position_source)])
    for child in _detail_children_from_command(config):
        detail.append(child)
    detail.append(link)

    return pytak.cot_event(
        uid=uid,
        cot_type=cot_type,
        stale=cot_stale,
        point=point,
        detail=detail,
        access=config.get("COT_ACCESS", pytak.DEFAULT_COT_ACCESS),
    )


def position_to_cot(
    gps_info: dict,
    config: Union[dict, SectionProxy, None] = None,
    known_gps_info: Optional[dict] = None,
) -> Optional[bytes]:
    """Convert position to CoT XML (TAK Protocol v0)."""
    del known_gps_info  # backward-compatible signature
    cot: Optional[Element] = position_to_cot_xml(gps_info, config)
    return pytak.serialize_cot(cot, trailing_newline=True) if cot is not None else None


def gpspipe_to_cot_xml(
    gps_info: dict,
    config: Union[dict, SectionProxy, None] = None,
) -> Optional[Element]:
    """Backward-compatible alias for position_to_cot_xml."""
    return position_to_cot_xml(gps_info, config)


def gpspipe_to_cot(
    gps_info: dict,
    config: Union[dict, SectionProxy, None] = None,
    known_gps_info: Optional[dict] = None,
) -> Optional[bytes]:
    """Backward-compatible alias for position_to_cot."""
    return position_to_cot(gps_info, config, known_gps_info)


def gen_sensor_cot(
    config=None,
    lat: float = 0.0,
    lon: float = 0.0,
    hae: float = 0.0,
    ce: str = "9999999.0",
    le: str = "9999999.0",
):
    """Generate a periodic sensor beacon CoT (a-f-G-E-S-E)."""
    config = config or {}
    sensor_id = config.get("SENSOR_ID", lincot.DEFAULT_SENSOR_ID)
    cot_type = config.get("SENSOR_COT_TYPE", lincot.DEFAULT_SENSOR_COT_TYPE)
    cot_stale = int(config.get("COT_STALE", pytak.DEFAULT_COT_STALE))
    callsign = config.get("SENSOR_CALLSIGN", sensor_id)
    payload_type = config.get("SENSOR_PAYLOAD_TYPE", lincot.DEFAULT_SENSOR_PAYLOAD_TYPE)

    contact = ET.Element("contact")
    contact.set("callsign", callsign)

    sensor_elem = ET.Element("sensor")
    sensor_elem.set("sensor_id", sensor_id)
    sensor_elem.set("type", payload_type)

    detail = pytak.cot_detail(contact, sensor_elem)

    return pytak.cot_event(
        lat=lat,
        lon=lon,
        hae=str(hae),
        ce=ce,
        le=le,
        uid=f"SENSOR.{sensor_id}",
        cot_type=cot_type,
        stale=cot_stale,
        detail=detail,
        access=config.get("COT_ACCESS", pytak.DEFAULT_COT_ACCESS),
    )
