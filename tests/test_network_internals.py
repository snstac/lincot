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

"""Tests for lincot.network internals (route parsing, sockets, ioctl)."""

import builtins
import socket

import pytest

from lincot import network

ROUTE_HEADER = (
    "Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\n"
)


class FakeSocket:
    """Minimal stand-in for socket.socket."""

    def __init__(self, ip="192.168.1.7", connect_error=None):
        self.ip = ip
        self.connect_error = connect_error
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True
        return False

    def connect(self, addr):
        """Raise the configured error, if any."""
        if self.connect_error:
            raise self.connect_error

    def getsockname(self):
        """Return the configured local address."""
        return (self.ip, 54321)

    def fileno(self):
        """Return a dummy file descriptor."""
        return 99

    def close(self):
        """Record that the socket was closed."""
        self.closed = True


@pytest.fixture
def linux(monkeypatch):
    """Pretend to run on Linux."""
    monkeypatch.setattr("lincot.network.sys.platform", "linux")


def _route_file(monkeypatch, tmp_path, body):
    """Redirect /proc/net/route reads to a temporary file."""
    route = tmp_path / "route"
    route.write_text(ROUTE_HEADER + body, encoding="utf-8")
    real_open = builtins.open

    def fake_open(path, *args, **kwargs):
        assert path == "/proc/net/route"
        return real_open(route, *args, **kwargs)

    monkeypatch.setattr("lincot.network.open", fake_open, raising=False)


def _packed(ip):
    """Build an ioctl SIOCGIFADDR result carrying ip at bytes 20..24."""
    return b"\x00" * 20 + socket.inet_aton(ip) + b"\x00" * 232


def test_default_route_interface_non_linux(monkeypatch):
    """Non-Linux platforms have no /proc route table."""
    monkeypatch.setattr("lincot.network.sys.platform", "darwin")
    assert network._default_route_interface() is None


def test_interface_ipv4_non_linux(monkeypatch):
    """Non-Linux platforms skip the ioctl lookup."""
    monkeypatch.setattr("lincot.network.sys.platform", "win32")
    assert network._interface_ipv4("eth0") is None


def test_default_route_interface_lowest_metric(monkeypatch, tmp_path, linux):
    """Lowest-metric default route wins; short and non-default lines skipped."""
    body = (
        "short\tline\n"
        "eth1\t0000A8C0\t00000000\t0001\t0\t0\t0\t00FFFFFF\t0\n"
        "wlan0\t00000000\t0101A8C0\t0003\t0\t0\t600\t00000000\t0\n"
        "eth0\t00000000\t0101A8C0\t0003\t0\t0\t100\t00000000\t0\n"
        "usb0\t00000000\t0101A8C0\t0003\t0\t0\t300\t00000000\t0\n"
    )
    _route_file(monkeypatch, tmp_path, body)
    assert network._default_route_interface() == "eth0"


def test_default_route_interface_no_default(monkeypatch, tmp_path, linux):
    """No default route yields None."""
    body = "eth1\t0000A8C0\t00000000\t0001\t0\t0\t0\t00FFFFFF\t0\n"
    _route_file(monkeypatch, tmp_path, body)
    assert network._default_route_interface() is None


def test_default_route_interface_oserror(monkeypatch, linux):
    """Unreadable route table yields None."""

    def fake_open(*args, **kwargs):
        raise OSError("nope")

    monkeypatch.setattr("lincot.network.open", fake_open, raising=False)
    assert network._default_route_interface() is None


def test_outbound_ipv4_success(monkeypatch):
    """Outbound socket local address is returned."""
    monkeypatch.setattr(
        "lincot.network.socket.socket", lambda *a: FakeSocket("10.1.2.3")
    )
    assert network._outbound_ipv4() == "10.1.2.3"


def test_outbound_ipv4_loopback(monkeypatch):
    """Loopback outbound addresses are rejected."""
    monkeypatch.setattr(
        "lincot.network.socket.socket", lambda *a: FakeSocket("127.0.1.1")
    )
    assert network._outbound_ipv4() is None


def test_outbound_ipv4_oserror(monkeypatch):
    """Socket errors yield None."""
    monkeypatch.setattr(
        "lincot.network.socket.socket",
        lambda *a: FakeSocket(connect_error=OSError("unreachable")),
    )
    assert network._outbound_ipv4() is None


def test_interface_ipv4_success(monkeypatch, linux):
    """ioctl result is decoded and the socket closed."""
    sock = FakeSocket()
    calls = []
    monkeypatch.setattr("lincot.network.socket.socket", lambda *a: sock)

    def fake_ioctl(fd, request, arg):
        calls.append((fd, request, arg[:4]))
        return _packed("192.168.1.7")

    monkeypatch.setattr("lincot.network.fcntl.ioctl", fake_ioctl)
    assert network._interface_ipv4("eth0") == "192.168.1.7"
    assert calls == [(99, 0x8915, b"eth0")]
    assert sock.closed


def test_interface_ipv4_oserror(monkeypatch, linux):
    """Interfaces without an address yield None and close the socket."""
    sock = FakeSocket()
    monkeypatch.setattr("lincot.network.socket.socket", lambda *a: sock)

    def fake_ioctl(*args):
        raise OSError("no address")

    monkeypatch.setattr("lincot.network.fcntl.ioctl", fake_ioctl)
    assert network._interface_ipv4("wlan0") is None
    assert sock.closed


def test_interface_ipv4_loopback(monkeypatch, linux):
    """Loopback interface addresses are rejected."""
    monkeypatch.setattr("lincot.network.socket.socket", lambda *a: FakeSocket())
    monkeypatch.setattr(
        "lincot.network.fcntl.ioctl", lambda *a: _packed("127.0.0.1")
    )
    assert network._interface_ipv4("lo") is None


def test_get_host_ip_falls_back_to_outbound(monkeypatch):
    """Outbound address is used when no interface has an IP."""
    monkeypatch.setattr("lincot.network._default_route_interface", lambda: None)
    monkeypatch.setattr("lincot.network._interface_ipv4", lambda name: None)
    monkeypatch.setattr("lincot.network._outbound_ipv4", lambda: "203.0.113.9")
    assert network.get_host_ip() == "203.0.113.9"


def test_is_localhost_host_edge_cases():
    """Empty values are not localhost; whitespace and case are normalised."""
    assert not network.is_localhost_host(None)
    assert not network.is_localhost_host("")
    assert network.is_localhost_host("  LocalHost  ")
    assert network.is_localhost_host(" ::1\n")
    assert not network.is_localhost_host("   ")
