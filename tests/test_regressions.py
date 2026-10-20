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

"""Regression tests for config parsing and CoT field bugs.

/etc/default/lincot is a systemd EnvironmentFile that the Cockpit plugin and
operators both edit, so ``POLL_INTERVAL=`` (empty) or a typo is a realistic
value. Before these fixes such a value raised ValueError inside a worker and
took the gateway down; now it falls back to the documented default.
"""

import asyncio
import logging

import pytest

import lincot
from lincot import classes
from lincot.functions import gen_sensor_cot, position_to_cot_xml
from lincot.position import static_tpv


def _sensor_worker(config):
    worker = classes.SensorWorker.__new__(classes.SensorWorker)
    worker.config = config
    worker._logger = logging.getLogger("test")
    return worker


def _lincot_worker(config):
    worker = classes.LincotWorker.__new__(classes.LincotWorker)
    worker.config = config
    worker._logger = logging.getLogger("test")
    worker._position_source = "gpsd"
    worker.status = classes._NoStatus()
    return worker


class _StopLoop(Exception):
    pass


async def _noop_put(_event):
    return None


@pytest.fixture
def no_gpsd(monkeypatch):
    monkeypatch.setattr(classes, "_gpsd", None)


# -- empty or invalid numeric settings fall back to defaults -----------------


@pytest.mark.parametrize("value", ["", "  ", "sixty"])
def test_sensor_period_bad_value_uses_default(monkeypatch, no_gpsd, value):
    slept = []

    async def _sleep(seconds):
        slept.append(seconds)
        raise _StopLoop

    worker = _sensor_worker({"SENSOR_KEEPALIVE_PERIOD": value})
    worker.put_queue = _noop_put
    monkeypatch.setattr(classes.asyncio, "sleep", _sleep)
    with pytest.raises(_StopLoop):
        asyncio.run(worker.run())
    assert slept == [lincot.DEFAULT_SENSOR_KEEPALIVE_PERIOD]


@pytest.mark.parametrize("value", ["", "abc"])
def test_poll_interval_bad_value_uses_default(monkeypatch, value):
    slept = []

    async def _sleep(seconds):
        slept.append(seconds)
        raise _StopLoop

    async def _heartbeat(*_args, **_kwargs):
        return None

    worker = _lincot_worker(
        {
            "COT_URL": "udp://239.2.3.1:6969",
            "POLL_INTERVAL": value,
            "STATIC_LAT": "1.0",
            "STATIC_LON": "2.0",
        }
    )
    worker.put_queue = _noop_put
    monkeypatch.setattr(worker, "_heartbeat", _heartbeat)
    monkeypatch.setattr(classes.asyncio, "sleep", _sleep)
    with pytest.raises(_StopLoop):
        asyncio.run(worker.run())
    assert slept == [lincot.DEFAULT_POLL_INTERVAL]


def test_gps_info_timeout_empty_uses_default(monkeypatch):
    seen = {}

    class _Proc:
        pid = 1
        returncode = 0

        async def communicate(self):
            return b'{"class":"TPV"}\n', b""

    async def _create(*_args, **_kwargs):
        return _Proc()

    async def _wait_for(coro, timeout):
        seen["timeout"] = timeout
        return await coro

    worker = _lincot_worker({"GPS_INFO_TIMEOUT": ""})
    worker.gps_info_cmd = "gpspipe"
    monkeypatch.setattr(classes.asyncio, "create_subprocess_shell", _create)
    monkeypatch.setattr(classes.asyncio, "wait_for", _wait_for)
    assert asyncio.run(worker._read_gps_output()) == '{"class":"TPV"}\n'
    assert seen["timeout"] == 15.0


def test_sensor_lat_lon_bad_value_falls_back(no_gpsd):
    worker = _sensor_worker(
        {"SENSOR_LAT": "north", "SENSOR_LON": "", "SENSOR_HAE": "x"}
    )
    lat, lon, hae, _ce, _le = asyncio.run(worker._get_position())
    assert (lat, lon, hae) == (0.0, 0.0, 0.0)


@pytest.mark.parametrize("value", ["", "abc"])
def test_cot_stale_bad_value_uses_default(value):
    tpv = {"class": "TPV", "lat": 1.0, "lon": 2.0}
    assert position_to_cot_xml(tpv, {"COT_STALE": value}) is not None
    assert gen_sensor_cot({"COT_STALE": value}) is not None


def test_empty_sensor_id_uses_default():
    cot = gen_sensor_cot({"SENSOR_ID": "", "SENSOR_CALLSIGN": ""})
    assert cot.get("uid") == f"SENSOR.{lincot.DEFAULT_SENSOR_ID}"
    assert cot.find(".//contact").get("callsign") == lincot.DEFAULT_SENSOR_ID


def test_invalid_static_position_is_not_a_crash():
    assert static_tpv({"STATIC_LAT": "abc", "STATIC_LON": "1.0"}) is None


def test_invalid_static_position_is_reported(monkeypatch):
    counted = []
    worker = _lincot_worker(
        {"COT_URL": "udp://x:1", "STATIC_LAT": "abc", "STATIC_LON": "1"}
    )
    worker.status.count = lambda name, *a: counted.append(name)

    async def _sleep(_seconds):
        raise _StopLoop

    async def _heartbeat(*_args, **_kwargs):
        return None

    monkeypatch.setattr(worker, "_heartbeat", _heartbeat)
    monkeypatch.setattr(classes.asyncio, "sleep", _sleep)
    with pytest.raises(_StopLoop):
        asyncio.run(worker.run())
    assert counted == ["bad_static_position"]


# -- receiver beacon follows a configured static position --------------------


def test_sensor_beacon_uses_static_position(no_gpsd):
    """A fixed site must not put its receiver marker at null island."""
    worker = _sensor_worker(
        {"STATIC_LAT": "45.0", "STATIC_LON": "-122.0", "STATIC_HAE": "100"}
    )
    lat, lon, hae, _ce, _le = asyncio.run(worker._get_position())
    assert (lat, lon, hae) == (45.0, -122.0, 100.0)


def test_sensor_position_overrides_static(no_gpsd):
    worker = _sensor_worker(
        {
            "SENSOR_LAT": "10.0",
            "SENSOR_LON": "20.0",
            "STATIC_LAT": "45.0",
            "STATIC_LON": "-122.0",
        }
    )
    lat, lon, _hae, _ce, _le = asyncio.run(worker._get_position())
    assert (lat, lon) == (10.0, 20.0)


# -- CoT fields -------------------------------------------------------------


def test_remarks_without_nsat_do_not_print_none():
    tpv = {"class": "TPV", "mode": 3, "lat": 1.0, "lon": 2.0, "uSat": 8}
    remarks = position_to_cot_xml(tpv, {}).find(".//remarks").text
    assert "None" not in remarks
    assert "8 sats used" in remarks


def test_zero_altitude_is_a_real_altitude():
    """altHAE 0.0 (sea level) is a value, not 'missing'."""
    tpv = {
        "class": "TPV",
        "mode": 3,
        "lat": 1.0,
        "lon": 2.0,
        "altHAE": 0.0,
        "altMSL": 31.0,
    }
    event = position_to_cot_xml(tpv, {})
    assert event.find("point").get("hae") == "0.0"
    assert event.find(".//__gps").get("alt_m") == "0.0"


def test_status_records_zero_altitude():
    recorded = {}
    worker = _lincot_worker({})
    worker.status.record = lambda **kw: recorded.update(kw)
    worker.put_queue = _noop_put
    tpv = {"class": "TPV", "mode": 3, "lat": 1.0, "lon": 2.0, "altHAE": 0.0,
           "altMSL": 31.0}
    asyncio.run(worker.handle_data(tpv))
    assert recorded["alt"] == 0.0


# -- receiver beacon gpsd accuracy ------------------------------------------


class _Packet:
    mode = 3

    def __init__(self, error):
        self.error = error

    def position(self):
        return 1.0, 2.0

    def altitude(self):
        return 3.0


def _fake_gpsd(packet):
    return type(
        "FakeGpsd", (), {"connect": staticmethod(lambda: None),
                         "get_current": staticmethod(lambda: packet)}
    )


def test_poll_gpsd_tolerates_error_none(monkeypatch):
    """gpsd-py3 can leave error unset; that must not discard a valid fix."""
    monkeypatch.setattr(classes, "_gpsd", _fake_gpsd(_Packet(None)))
    assert classes.SensorWorker._poll_gpsd() == (
        1.0, 2.0, 3.0, "9999999.0", "9999999.0"
    )


def test_poll_gpsd_keeps_zero_error(monkeypatch):
    monkeypatch.setattr(classes, "_gpsd", _fake_gpsd(_Packet({"x": 0.0, "v": 0})))
    _lat, _lon, _hae, ce, le = classes.SensorWorker._poll_gpsd()
    assert (ce, le) == ("0.0", "0")


# -- review follow-ups ------------------------------------------------------


def test_missing_altitude_is_blank_not_none():
    event = position_to_cot_xml({"class": "TPV", "mode": 2, "lat": 1.0, "lon": 2.0})
    assert event.find(".//__gps").get("alt_m") == ""
    assert event.find("point").get("hae") == "9999999.0"


def test_numeric_dict_values_still_accepted():
    """Library callers passing real numbers must keep working (int(7200.0))."""
    tpv = {"class": "TPV", "lat": 1.0, "lon": 2.0}
    event = position_to_cot_xml(tpv, {"COT_STALE": 7200.0})
    sensor = gen_sensor_cot({"COT_STALE": 7200.0})
    for cot in (event, sensor):
        assert cot.get("stale") > cot.get("start")
    from lincot.settings import config_number

    assert config_number({"X": 7200.0}, "X", 1, cast=int) == 7200


def test_partial_sensor_position_beats_static(no_gpsd):
    worker = _sensor_worker(
        {"SENSOR_LAT": "1.0", "STATIC_LAT": "45.0", "STATIC_LON": "-122.0"}
    )
    lat, lon, _hae, _ce, _le = asyncio.run(worker._get_position())
    assert (lat, lon) == (1.0, 0.0)


def test_invalid_sensor_position_falls_back_to_static(no_gpsd):
    worker = _sensor_worker(
        {
            "SENSOR_LAT": "x",
            "SENSOR_LON": "y",
            "STATIC_LAT": "45.0",
            "STATIC_LON": "-122.0",
        }
    )
    lat, lon, _hae, _ce, _le = asyncio.run(worker._get_position())
    assert (lat, lon) == (45.0, -122.0)


@pytest.mark.parametrize(
    "lat,lon", [("nan", "1"), ("1", "inf"), ("91", "0"), ("0", "-181")]
)
def test_unusable_static_coordinates_rejected(lat, lon):
    assert static_tpv({"STATIC_LAT": lat, "STATIC_LON": lon}) is None
