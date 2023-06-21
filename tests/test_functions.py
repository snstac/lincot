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

import io
import xml.etree.ElementTree as ET

import pytest

from lincot.functions import gpspipe_to_cot, gpspipe_to_cot_xml


__author__ = "Greg Albrecht <oss@undef.net>"
__copyright__ = "Copyright 2023 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


@pytest.fixture
def sample_gps_info():
    return {
        "class": "TPV",
        "device": "/dev/ttyACM0",
        "mode": 3,
        "time": "2023-06-14T17:32:03.000Z",
        "leapseconds": 18,
        "ept": 0.005,
        "lat": 37.760050100,
        "lon": -122.497702900,
        "altHAE": 20.6260,
        "altMSL": 50.4830,
        "alt": 50.4830,
        "epx": 29.761,
        "epy": 55.948,
        "epv": 13.519,
        "track": 359.4589,
        "magtrack": 12.7281,
        "magvar": 13.3,
        "speed": 0.027,
        "climb": 0.000,
        "eps": 1.83,
        "epc": 27.04,
        "ecefx": -2712542.94,
        "ecefy": -4258214.64,
        "ecefz": 3884445.11,
        "ecefvx": 0.31,
        "ecefvy": 0.53,
        "ecefvz": 0.77,
        "ecefpAcc": 30.17,
        "ecefvAcc": 1.83,
        "geoidSep": -29.900,
        "eph": 21.721,
        "sep": 103.170,
    }


def test_gpspipe_to_cot_xml(sample_gps_info):
    """Test converting GPS Info to CoT XML."""
    cot = gpspipe_to_cot_xml(sample_gps_info)
    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-G-E-S"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.7600501"
    assert point[0].attrib["lon"] == "-122.4977029"
    assert point[0].attrib["hae"] == "20.626"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "359.4589"
    assert track[0].attrib["speed"] == "0.027"


def test_gpspipe_to_cot(sample_gps_info):
    """Test converting GPS Info to CoT."""
    cot: bytes = gpspipe_to_cot(sample_gps_info)
    assert b"a-f-G-E-S" in cot
    assert b"LINCOT" in cot
