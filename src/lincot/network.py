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

"""Network helpers for choosing a reachable host address."""

import fcntl
import socket
import struct
import sys
from typing import Optional, Sequence

WIFI_INTERFACE_NAMES: Sequence[str] = ("wifi0", "wlan0")

_LOCALHOST_NAMES = frozenset({"localhost", "127.0.0.1", "::1"})


def _default_route_interface() -> Optional[str]:
    """Return the interface name for the lowest-metric default IPv4 route."""
    if sys.platform != "linux":
        return None

    best_iface: Optional[str] = None
    best_metric: Optional[int] = None

    try:
        with open("/proc/net/route", encoding="utf-8") as handle:
            next(handle, None)
            for line in handle:
                fields = line.strip().split()
                if len(fields) < 8:
                    continue
                iface, destination, _gateway, _flags, _refcnt, _use, metric = fields[:7]
                if destination != "00000000":
                    continue
                metric_value = int(metric)
                if best_metric is None or metric_value < best_metric:
                    best_metric = metric_value
                    best_iface = iface
    except OSError:
        return None

    return best_iface


def _outbound_ipv4() -> Optional[str]:
    """Return the local IPv4 address chosen for outbound traffic."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("203.0.113.1", 80))
            ip = sock.getsockname()[0]
    except OSError:
        return None
    if ip.startswith("127."):
        return None
    return ip


def _interface_ipv4(name: str) -> Optional[str]:
    """Return the IPv4 address assigned to an interface, if any."""
    if sys.platform != "linux":
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        packed = fcntl.ioctl(
            sock.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", name.encode()[:15]),
        )
    except OSError:
        return None
    finally:
        sock.close()

    ip = socket.inet_ntoa(packed[20:24])
    if ip.startswith("127."):
        return None
    return ip


def get_host_ip() -> Optional[str]:
    """Prefer the default-route interface IP, then WiFi interface IPs."""
    iface = _default_route_interface()
    if iface:
        ip = _interface_ipv4(iface)
        if ip:
            return ip

    for wifi_iface in WIFI_INTERFACE_NAMES:
        ip = _interface_ipv4(wifi_iface)
        if ip:
            return ip

    return _outbound_ipv4()


def is_localhost_host(host: Optional[str]) -> bool:
    """Return True when host refers to this machine via loopback."""
    if not host:
        return False
    return host.strip().lower() in _LOCALHOST_NAMES
