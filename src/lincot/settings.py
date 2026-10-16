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

"""Tolerant readers for numeric LINCOT settings."""

import logging
from configparser import SectionProxy
from typing import Callable, Optional, TypeVar, Union

Number = TypeVar("Number", int, float)

_logger = logging.getLogger(__name__)


def config_number(
    config: Union[dict, SectionProxy, None],
    key: str,
    default: Number,
    cast: Callable[[str], Number] = float,
    minimum: Optional[Number] = None,
) -> Number:
    """Return ``config[key]`` as a number, or ``default`` if unset or invalid.

    /etc/default/lincot is a systemd EnvironmentFile edited by hand and by the
    Cockpit plugin, so ``POLL_INTERVAL=`` (empty) or a typo is a realistic
    value. Raising on it would take the gateway down over one bad setting;
    falling back to the documented default keeps it reporting.
    """
    raw = (config or {}).get(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            value = cast(raw)
        else:
            value = cast(str(raw).strip())
    except (ValueError, OverflowError):
        _logger.warning("Ignoring invalid %s=%r; using %s", key, raw, default)
        return default
    if minimum is not None and value < minimum:
        _logger.warning("Ignoring %s=%r below %s; using %s", key, raw, minimum, default)
        return default
    return value
