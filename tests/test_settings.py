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

"""Tests for tolerant numeric setting parsing."""

from configparser import ConfigParser

import pytest

from lincot.position import first_present
from lincot.settings import config_number


@pytest.mark.parametrize("config", [None, {}, {"X": None}, {"X": ""}, {"X": "  "}])
def test_unset_returns_default(config):
    assert config_number(config, "X", 7, cast=int) == 7


def test_valid_values_are_cast():
    assert config_number({"X": " 42 "}, "X", 7, cast=int) == 42
    assert config_number({"X": "2.5"}, "X", 1.0) == 2.5
    assert config_number({"X": 3}, "X", 1, cast=int) == 3


def test_invalid_value_returns_default_and_warns(caplog):
    assert config_number({"X": "abc"}, "X", 7, cast=int) == 7
    assert "Ignoring invalid X" in caplog.text


def test_below_minimum_returns_default_and_warns(caplog):
    assert config_number({"X": "0"}, "X", 61, cast=int, minimum=1) == 61
    assert config_number({"X": "-5"}, "X", 61, cast=int, minimum=1) == 61
    assert config_number({"X": "1"}, "X", 61, cast=int, minimum=1) == 1
    assert "below 1" in caplog.text


def test_reads_configparser_section():
    parser = ConfigParser()
    parser.read_string("[lincot]\nPOLL_INTERVAL =\nCOT_STALE = 90\n")
    section = parser["lincot"]
    assert config_number(section, "POLL_INTERVAL", 61, cast=int) == 61
    assert config_number(section, "COT_STALE", 3600, cast=int) == 90


def test_first_present_keeps_zero():
    assert first_present(0.0, 31.0) == 0.0
    assert first_present(None, "", 31.0) == 31.0
    assert first_present(None, "  ") is None
