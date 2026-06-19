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

"""LINCOT Function Tests."""

import xml.etree.ElementTree as ET

import pytest
import pytak

from lincot.functions import gpspipe_to_cot, position_to_cot_xml
from lincot.identity import get_callsign, get_uid
from lincot.position import static_position_configured, static_tpv

if not hasattr(pytak, "truncate_float"):

    def _truncate_float(value):
        whole, fraction = str(value).split(".", 1)
        fraction = fraction[:4].rstrip("0")
        return whole if not fraction else f"{whole}.{fraction}"

    pytak.truncate_float = _truncate_float


@pytest.fixture
def sample_gps_info():
    return {
        "class": "TPV",
        "device": "/dev/ttyACM0",
        "mode": 3,
        "time": "2023-06-14T17:32:03.000Z",
        "lat": 37.760050100,
        "lon": -122.497702900,
        "altHAE": 20.6260,
        "epx": 3.0,
        "epy": 4.0,
        "epv": 6.5,
        "track": 359.4589,
        "speed": 0.027,
    }


@pytest.fixture
def sample_config():
    return {
        "CALLSIGN": "edge-node-1",
        "COT_UID": "abc123def4567890abc123def4567890",
        "COT_URL": "udp://239.2.3.1:6969",
        "COCKPIT_URL": "http://edge-node-1.local:9090/",
        "SSH_USER": "pi",
    }


def test_gpspipe_to_cot_xml(sample_gps_info, sample_config):
    """Test converting GPS Info to CoT XML."""
    cot = position_to_cot_xml(sample_gps_info, sample_config)
    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-G-E-S"
    assert cot.attrib["uid"] == sample_config["COT_UID"]

    point = cot.findall("point")
    assert point[0].attrib["lat"] == "37.76"
    assert point[0].attrib["lon"] == "-122.4977"
    assert point[0].attrib["hae"] == "20.626"
    assert point[0].attrib["ce"] == "5.0"
    assert point[0].attrib["le"] == "6.5"

    detail = cot.findall("detail")[0]
    track = detail.findall("track")[0]
    assert track.attrib["course"] == "359.4589"
    assert track.attrib["speed"] == "0.027"

    contact = detail.findall("contact")[0]
    assert contact.attrib["callsign"] == "edge-node-1"

    remarks = detail.findall("remarks")[0]
    assert "Cockpit:" in remarks.text
    assert "SSH:" in remarks.text

    link = detail.findall("link")[0]
    assert link.attrib["url"] == "http://edge-node-1.local:9090"
    assert link.attrib["relation"] == "r-u"


def test_gpspipe_to_cot(sample_gps_info, sample_config):
    """Test converting GPS Info to CoT bytes."""
    cot: bytes = gpspipe_to_cot(sample_gps_info, sample_config)
    assert b"a-f-G-E-S" in cot
    assert sample_config["COT_UID"].encode() in cot
    assert b"edge-node-1" in cot


def test_gpspipe_to_cot_prefers_eph(sample_gps_info, sample_config):
    """gpsd eph is used directly for CoT circular error when present."""
    sample_gps_info["eph"] = 2.25
    cot = position_to_cot_xml(sample_gps_info, sample_config)
    point = cot.findall("point")[0]
    assert point.attrib["ce"] == "2.25"


def test_remarks_extra_cmd(sample_gps_info, sample_config, tmp_path):
    """Dynamic command output is appended to remarks."""
    script = tmp_path / "remarks.sh"
    script.write_text("#!/bin/sh\necho 'CPU: 12%'\necho 'Mem: 42%'\n", encoding="utf-8")
    script.chmod(0o755)
    sample_config["REMARKS_EXTRA_CMD"] = str(script)
    cot = position_to_cot_xml(sample_gps_info, sample_config)
    remarks = cot.findall("detail")[0].findall("remarks")[0]
    assert "CPU: 12%" in remarks.text
    assert "Mem: 42%" in remarks.text


def test_cot_detail_xml_cmd(sample_gps_info, sample_config, tmp_path):
    """Dynamic XML command output is appended as structured CoT detail."""
    script = tmp_path / "detail.sh"
    script.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' '<aryaos version=\"1\"><host name=\"edge-node-1\" /></aryaos>'\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    sample_config["COT_DETAIL_XML_CMD"] = str(script)
    cot = position_to_cot_xml(sample_gps_info, sample_config)
    aryaos = cot.findall("detail")[0].findall("aryaos")[0]
    assert aryaos.attrib["version"] == "1"
    assert aryaos.findall("host")[0].attrib["name"] == "edge-node-1"


def test_cot_detail_xml_cmd_ignores_invalid_xml(sample_gps_info, sample_config, tmp_path):
    """Invalid dynamic XML output should not prevent normal CoT generation."""
    script = tmp_path / "detail.sh"
    script.write_text("#!/bin/sh\necho '<aryaos><broken></aryaos>'\n", encoding="utf-8")
    script.chmod(0o755)
    sample_config["COT_DETAIL_XML_CMD"] = str(script)
    cot = position_to_cot_xml(sample_gps_info, sample_config)
    detail = cot.findall("detail")[0]
    assert detail.findall("aryaos") == []
    assert detail.findall("remarks")


def test_static_tpv():
    """Static coordinates produce a TPV dict."""
    config = {"STATIC_LAT": "45.0", "STATIC_LON": "-122.0", "STATIC_HAE": "100.0"}
    assert static_position_configured(config)
    tpv = static_tpv(config)
    assert tpv["class"] == "TPV"
    assert tpv["lat"] == 45.0
    assert tpv["lon"] == -122.0


def test_get_callsign_defaults_to_hostname(monkeypatch):
    """Callsign defaults to hostname when unset."""
    monkeypatch.setattr("lincot.identity.get_hostname", lambda: "myhost")
    assert get_callsign({}) == "myhost"
    assert get_callsign({"CALLSIGN": "custom"}) == "custom"


def test_get_uid_from_config():
    """UID honors COT_UID override."""
    uid = "deadbeefdeadbeefdeadbeefdeadbeef"
    assert get_uid({"COT_UID": uid}) == uid
