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

"""LINCOT functions for parsing gpspipe and generating Cursor on Target."""

from configparser import SectionProxy
from typing import Optional, Union
from uuid import getnode
from xml.etree.ElementTree import tostring, Element

import pytak
import lincot

__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright 2023 Sensors & Signals LLC"
__license__ = "Apache License, Version 2.0"


def create_tasks(config: Union[dict, SectionProxy], clitool: pytak.CLITool) -> set:
    """Bootstrap a set of coroutine tasks for a PyTAK application.

    Bootstrapped tasks:
        1) Receive Queue Worker
        2) Transmit Queue Worker

    This application adds:
        `lincot.LincotWorker`

    Parameters
    ----------
    config : `dict`, `SectionProxy`
        `dict` or `SectionProxy` of configuration parameters & values.
    clitool : `pytak.CLITool`
        PyTAK CLITool instance.

    Returns
    -------
    `set`
        Set of coroutine tasks.
    """
    return set([lincot.LincotWorker(clitool.tx_queue, config)])


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def gpspipe_to_cot_xml(
    gps_info: dict,
    config: Union[dict, SectionProxy, None] = None,
) -> Optional[Element]:
    """Convert GPS Info to Cursor on Target.

    Parameters
    ----------
    gps_info : GPS Info from the command line.
    config : Configuration parameters for LINCOT.

    Returns
    -------
    A Cursor on Target <event/>.
    """
    config = config or {}
    remarks_fields: list = []

    if gps_info.get("class") != "TPV":
        return None

    lat = gps_info.get("lat")
    lon = gps_info.get("lon")

    if not all([lat, lon]):
        return None

    # N.B. SectionProxy does not support dict's "fallback" parameter, you have to
    #      use explicit conditionals ('or'), like so:
    cot_type: str = str(config.get("COT_TYPE") or lincot.DEFAULT_COT_TYPE)
    cot_stale: int = int(config.get("COT_STALE") or lincot.DEFAULT_COT_STALE)
    cot_callsign: str = config.get("CALLSIGN") or f"LINCOT-{getnode()}"
    uid: str = f"LINCOT-{cot_callsign}"

    cot_host_id: str = str(config.get("COT_HOST_ID") or "")

    point = Element("point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", str(gps_info.get("altHAE") or "9999999.0"))
    point.set("le", "9999999.0")
    point.set("ce", "9999999.0")

    track: Element = Element("track")
    track.set("course", str(gps_info.get("track")))

    # CoT Speed is meters/second
    track.set("speed", str(gps_info.get("speed")))

    # Contact
    contact: Element = Element("contact")
    contact.set("callsign", str(cot_callsign))

    remarks: Element = Element("remarks")
    remarks_fields.append(f"{cot_host_id}")
    _remarks = " ".join(list(filter(None, remarks_fields)))
    remarks.text = _remarks

    detail = Element("detail")
    detail.append(track)
    detail.append(contact)
    detail.append(remarks)

    root: Element = Element("event")
    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", uid)
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(cot_stale))

    root.append(point)
    root.append(detail)

    return root


def gpspipe_to_cot(
    gps_info: dict,
    config: Union[dict, SectionProxy, None] = None,
    known_gps_info: Optional[dict] = None,
) -> Optional[bytes]:
    """Convert AIS to CoT XML and return it as 'TAK Protocol, Version 0'.

    'TAK Protocol, Version 0' being:
     1. XML Declaration.
     2. Newline.
     3. Cursor on Target <event/> Element.
     4. Newline.
    """
    cot: Optional[Element] = gpspipe_to_cot_xml(gps_info, config)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, tostring(cot), b""]) if cot else None
    )
