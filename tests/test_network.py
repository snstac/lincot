#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Greg Albrecht <oss@undef.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Network helper tests."""

from lincot.network import get_host_ip, is_localhost_host
from lincot.remarks import get_cockpit_url


def test_is_localhost_host():
    """Loopback hostnames are detected."""
    assert is_localhost_host("localhost")
    assert is_localhost_host("127.0.0.1")
    assert is_localhost_host("::1")
    assert not is_localhost_host("192.168.1.10")
    assert not is_localhost_host("edge-node-1.local")


def test_get_cockpit_url_uses_host_ip(monkeypatch):
    """Default Cockpit URL uses a reachable interface IP."""
    monkeypatch.setattr("lincot.remarks.get_host_ip", lambda: "192.168.1.42")
    assert get_cockpit_url({}) == "http://192.168.1.42:9090/"


def test_get_cockpit_url_replaces_localhost_override(monkeypatch):
    """Configured localhost Cockpit URLs are rewritten to the host IP."""
    monkeypatch.setattr("lincot.remarks.get_host_ip", lambda: "10.0.0.5")
    assert get_cockpit_url({"COCKPIT_URL": "http://localhost:9090"}) == "http://10.0.0.5:9090/"


def test_get_cockpit_url_keeps_explicit_override():
    """Non-localhost COCKPIT_URL overrides are preserved."""
    url = "http://edge-node-1.local:9090/"
    assert get_cockpit_url({"COCKPIT_URL": url}) == url


def test_get_cockpit_url_falls_back_to_hostname(monkeypatch):
    """Use mDNS hostname when no interface IP is available."""
    monkeypatch.setattr("lincot.remarks.get_host_ip", lambda: None)
    monkeypatch.setattr("lincot.remarks.get_hostname", lambda: "aryaos")
    assert get_cockpit_url({}) == "http://aryaos.local:9090/"


def test_get_host_ip_prefers_default_route_interface(monkeypatch):
    """Default-route interface IP wins over WiFi fallbacks."""
    monkeypatch.setattr("lincot.network._default_route_interface", lambda: "eth0")
    monkeypatch.setattr(
        "lincot.network._interface_ipv4",
        lambda name: {"eth0": "192.168.1.10", "wifi0": "10.0.0.2"}.get(name),
    )
    monkeypatch.setattr("lincot.network._outbound_ipv4", lambda: "203.0.113.9")
    assert get_host_ip() == "192.168.1.10"


def test_get_host_ip_falls_back_to_wifi0(monkeypatch):
    """wifi0 is used when the default-route interface has no address."""
    monkeypatch.setattr("lincot.network._default_route_interface", lambda: "eth0")
    monkeypatch.setattr(
        "lincot.network._interface_ipv4",
        lambda name: {"wifi0": "10.0.0.2"}.get(name),
    )
    monkeypatch.setattr("lincot.network._outbound_ipv4", lambda: None)
    assert get_host_ip() == "10.0.0.2"
