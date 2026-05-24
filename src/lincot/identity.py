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

"""Host identity helpers for LINCOT CoT events."""

import re
import socket
from configparser import SectionProxy
from typing import Optional, Union

import lincot

_MACHINE_ID_RE = re.compile(r"^[a-f0-9]{32}$")


def get_hostname() -> str:
    """Return the system hostname (short name, no domain)."""
    name = socket.gethostname().strip()
    if "." in name:
        return name.split(".", maxsplit=1)[0]
    return name or "localhost"


def get_machine_id() -> Optional[str]:
    """Read Linux machine-id, if present and valid."""
    for path in lincot.MACHINE_ID_PATHS:
        try:
            with open(path, encoding="utf-8") as handle:
                value = handle.read().strip().lower()
        except OSError:
            continue
        if _MACHINE_ID_RE.match(value):
            return value
    return None


def get_callsign(config: Union[dict, SectionProxy, None]) -> str:
    """Callsign for contact element; defaults to hostname."""
    config = config or {}
    override = config.get("CALLSIGN")
    if override is not None and str(override).strip():
        return str(override).strip()
    return get_hostname()


def get_uid(config: Union[dict, SectionProxy, None]) -> str:
    """Stable CoT event uid; defaults to machine-id."""
    config = config or {}
    override = config.get("COT_UID")
    if override is not None and str(override).strip():
        return str(override).strip()
    machine_id = get_machine_id()
    if machine_id:
        return machine_id
    return f"lincot-{get_hostname()}"
