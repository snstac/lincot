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

"""Build CoT remarks and related URLs for edge nodes."""

from configparser import SectionProxy
import shlex
import subprocess
from typing import Union
from urllib.parse import urlparse

import pytak

import lincot
from lincot.identity import get_hostname, get_machine_id
from lincot.network import get_host_ip, is_localhost_host


def _cockpit_host(_config: Union[dict, SectionProxy, None]) -> str:
    """Host for Cockpit URL; never localhost when an interface IP is available."""
    ip = get_host_ip()
    if ip:
        return ip
    hostname = get_hostname()
    if hostname.lower() != "localhost":
        return f"{hostname}.local"
    return "0.0.0.0"


def get_cockpit_url(config: Union[dict, SectionProxy, None]) -> str:
    """Cockpit web UI URL for this host."""
    config = config or {}
    override = config.get("COCKPIT_URL")
    if override is not None and str(override).strip():
        parsed = urlparse(str(override).strip())
        if is_localhost_host(parsed.hostname):
            host = _cockpit_host(config)
            port = parsed.port or lincot.DEFAULT_COCKPIT_PORT
            scheme = parsed.scheme or "http"
            return f"{scheme}://{host}:{port}/"
        return str(override).strip().rstrip("/") + "/"
    host = _cockpit_host(config)
    return f"http://{host}:{lincot.DEFAULT_COCKPIT_PORT}/"


def _extra_from_command(config: Union[dict, SectionProxy, None]) -> str:
    """Run an optional remarks command and return stdout for remarks."""
    config = config or {}
    command = str(config.get("REMARKS_EXTRA_CMD") or "").strip()
    if not command:
        return ""
    try:
        timeout = float(
            config.get("REMARKS_EXTRA_CMD_TIMEOUT")
            or lincot.DEFAULT_REMARKS_EXTRA_CMD_TIMEOUT
        )
    except (TypeError, ValueError):
        timeout = lincot.DEFAULT_REMARKS_EXTRA_CMD_TIMEOUT
    try:
        run = subprocess.run(
            shlex.split(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return ""
    if run.returncode != 0:
        return ""
    return (run.stdout or "").strip()


def build_remarks(
    config: Union[dict, SectionProxy, None],
    *,
    position_source: str,
) -> str:
    """Multi-line remarks with host, connect, and TAK info."""
    config = config or {}
    hostname = get_hostname()
    machine_id = get_machine_id()
    ssh_user = str(config.get("SSH_USER") or lincot.DEFAULT_SSH_USER).strip()
    cockpit_url = get_cockpit_url(config)
    cot_url = pytak.sanitize_url_credentials(str(config.get("COT_URL") or ""))
    cot_host_id = str(config.get("COT_HOST_ID") or f"lincot@{hostname}")
    extra = str(config.get("REMARKS_EXTRA") or "").strip()
    command_extra = _extra_from_command(config)

    lines = [
        f"Host: {hostname}",
        f"Position: {position_source}",
    ]
    if machine_id:
        lines.append(f"Machine-ID: {machine_id[:8]}…")
    lines.append(f"Cockpit: {cockpit_url}")
    lines.append(f"SSH: ssh {ssh_user}@{hostname}.local")
    if cot_url:
        lines.append(f"TAK: {cot_url}")
    if cot_host_id:
        lines.append(f"Source: {cot_host_id}")
    if extra:
        lines.append(extra)
    if command_extra:
        lines.append(command_extra)
    lines.append(f"(via lincot@{hostname})")
    return "\n".join(lines)
