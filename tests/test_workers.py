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

"""Worker-level tests for LincotWorker and SensorWorker.

Coroutines are driven with ``asyncio.run()`` (see tests/test_status.py for
why bare ``async def`` tests are avoided). Everything is hermetic: no real
subprocess, gpsd, network or /run writes.
"""

import asyncio
import logging
import types
import xml.etree.ElementTree as ET

import pytest

from lincot import classes


class _StopLoop(Exception):
    pass


async def _noop_put(_event):
    return None


async def _stop_sleep(_seconds):
    raise _StopLoop


class _RecordingStatus(classes._NoStatus):
    """A _NoStatus that remembers counters and writes."""

    def __init__(self):
        self.counts = []
        self.writes = []
        self.sets = []

    def count(self, name, *args, **kwargs):
        self.counts.append(name)

    def set(self, *args, **kwargs):
        self.sets.append(kwargs)

    def write(self, *args, **kwargs):
        self.writes.append(kwargs)
        return False


def _lincot_worker(config=None):
    worker = classes.LincotWorker.__new__(classes.LincotWorker)
    worker.config = config if config is not None else {}
    worker._logger = logging.getLogger("test")
    worker._position_source = "gpsd"
    worker.status = _RecordingStatus()
    worker.put_queue = _noop_put
    worker.gps_info_cmd = "gpspipe --json -n 5"
    return worker


def _sensor_worker(config=None):
    worker = classes.SensorWorker.__new__(classes.SensorWorker)
    worker.config = config if config is not None else {}
    worker._logger = logging.getLogger("test")
    worker.put_queue = _noop_put
    return worker


class _Proc:
    pid = 4242

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self._out = (stdout, stderr)

    async def communicate(self):
        return self._out


def _patch_subprocess(monkeypatch, proc):
    async def _create(*_args, **_kwargs):
        return proc

    monkeypatch.setattr(classes.asyncio, "create_subprocess_shell", _create)


# -- _NoStatus ---------------------------------------------------------------


def test_no_status_every_method_is_a_no_op():
    status = classes._NoStatus()
    assert status.count("rx") is None
    assert status.record(fix="3D") is None
    assert status.set(source="gpsd") is None
    assert status.set_health("ok", "fine") is None
    assert status.set_input(source="gpsd") is None
    assert status.set_output("connected") is None
    assert status.write() is False
    assert status.write(force=True) is False


# -- LincotWorker.__init__ ---------------------------------------------------


def _construct(config):
    async def _build():
        return classes.LincotWorker(asyncio.Queue(), config)

    return asyncio.run(_build())


def test_constructor_static_config_sets_static_source(monkeypatch):
    monkeypatch.setattr(classes, "_StatusWriter", None)
    worker = _construct({"STATIC_LAT": "1.0", "STATIC_LON": "2.0"})
    assert worker._position_source == "static"
    assert isinstance(worker.status, classes._NoStatus)


def test_constructor_without_static_keeps_gpsd_source(monkeypatch):
    monkeypatch.setattr(classes, "_StatusWriter", None)
    worker = _construct({})
    assert worker._position_source == "gpsd"
    assert isinstance(worker.status, classes._NoStatus)


# -- get_gps_info ------------------------------------------------------------


def test_get_gps_info_timeout_is_counted(monkeypatch):
    worker = _lincot_worker()

    async def _timeout():
        raise asyncio.TimeoutError

    monkeypatch.setattr(worker, "_read_gps_output", _timeout)
    asyncio.run(worker.get_gps_info())
    assert worker.status.counts == ["gps_cmd_timeout"]
    assert len(worker.status.writes) == 1


def test_get_gps_info_empty_output_is_counted(monkeypatch):
    worker = _lincot_worker()

    async def _empty():
        return ""

    monkeypatch.setattr(worker, "_read_gps_output", _empty)
    asyncio.run(worker.get_gps_info())
    assert worker.status.counts == ["gps_no_output"]
    assert len(worker.status.writes) == 1


def test_get_gps_info_merges_sky_into_tpv(monkeypatch):
    worker = _lincot_worker()
    received = []

    async def _output():
        return (
            '{"class":"VERSION"}\n'
            '{"class":"SKY","uSat":7,"nSat":12,"hdop":1.1}\n'
            '{"class":"TPV","mode":3,"lat":1.0,"lon":2.0}\n'
        )

    async def _handle(data):
        received.append(data)

    monkeypatch.setattr(worker, "_read_gps_output", _output)
    monkeypatch.setattr(worker, "handle_data", _handle)
    asyncio.run(worker.get_gps_info())

    assert len(received) == 1
    assert received[0]["class"] == "TPV"
    assert received[0]["uSat"] == 7
    assert received[0]["nSat"] == 12


# -- _read_gps_output --------------------------------------------------------


def test_read_gps_output_returns_stdout(monkeypatch):
    worker = _lincot_worker()
    _patch_subprocess(monkeypatch, _Proc(stdout=b"hello\n"))
    assert asyncio.run(worker._read_gps_output()) == "hello\n"


def test_read_gps_output_nonzero_exit_raises_with_stderr(monkeypatch):
    worker = _lincot_worker()
    _patch_subprocess(monkeypatch, _Proc(returncode=2, stderr=b" no gpsd \n"))
    with pytest.raises(OSError, match="^no gpsd$"):
        asyncio.run(worker._read_gps_output())


def test_read_gps_output_nonzero_exit_without_stderr(monkeypatch):
    worker = _lincot_worker()
    _patch_subprocess(monkeypatch, _Proc(returncode=3))
    with pytest.raises(OSError, match="command exited 3"):
        asyncio.run(worker._read_gps_output())


def test_read_gps_output_timeout_survives_vanished_process_group(monkeypatch):
    worker = _lincot_worker({"GPS_INFO_TIMEOUT": "0.01"})
    proc = _Proc()
    killed = []

    async def _wait_for(coro, _timeout):
        coro.close()
        raise asyncio.TimeoutError

    def _killpg(pid, sig):
        killed.append((pid, sig))
        raise ProcessLookupError

    _patch_subprocess(monkeypatch, proc)
    monkeypatch.setattr(classes.asyncio, "wait_for", _wait_for)
    monkeypatch.setattr(classes.os, "killpg", _killpg)
    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(worker._read_gps_output())
    assert killed == [(proc.pid, classes.signal.SIGKILL)]


# -- run() -------------------------------------------------------------------


def test_run_without_cot_url_returns_early(monkeypatch):
    worker = _lincot_worker({})
    monkeypatch.setattr(classes.asyncio, "sleep", _stop_sleep)
    assert asyncio.run(worker.run()) is None
    assert worker.status.writes == []


def test_run_gpsd_mode_polls_then_sleeps_and_cancels_heartbeat(monkeypatch):
    worker = _lincot_worker({"COT_URL": "udp://239.2.3.1:6969"})
    calls = []
    state = {}

    async def _get_gps_info():
        calls.append("gps")

    async def _heartbeat(*_args, **_kwargs):
        state["started"] = True
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            state["cancelled"] = True
            raise

    real_sleep = asyncio.sleep

    async def _sleep(seconds):
        calls.append(("sleep", seconds))
        # Let the heartbeat task start so cancellation is observable.
        await real_sleep(0)
        raise _StopLoop

    async def _drive():
        with pytest.raises(_StopLoop):
            await worker.run()
        # Give the cancelled heartbeat a turn to process cancellation.
        await real_sleep(0)

    monkeypatch.setattr(worker, "get_gps_info", _get_gps_info)
    monkeypatch.setattr(worker, "_heartbeat", _heartbeat)
    monkeypatch.setattr(classes.asyncio, "sleep", _sleep)
    asyncio.run(_drive())

    assert calls == ["gps", ("sleep", classes.lincot.DEFAULT_POLL_INTERVAL)]
    assert worker.gps_info_cmd == classes.lincot.DEFAULT_GPS_INFO_CMD
    assert worker._position_source == "gpsd"
    assert worker.status.writes[0] == {"force": True}
    assert state == {"started": True, "cancelled": True}


# -- SensorWorker ------------------------------------------------------------


def test_sensor_run_puts_serialized_cot(monkeypatch):
    worker = _sensor_worker({"SENSOR_KEEPALIVE_PERIOD": "5"})
    sent = []
    cot = ET.Element("event", {"uid": "x"})

    async def _put(event):
        sent.append(event)

    async def _position():
        return 1.0, 2.0, 3.0, "4", "5"

    worker.put_queue = _put
    monkeypatch.setattr(worker, "_get_position", _position)
    monkeypatch.setattr(
        classes.lincot, "gen_sensor_cot", lambda config, *pos: cot
    )
    monkeypatch.setattr(classes.asyncio, "sleep", _stop_sleep)
    with pytest.raises(_StopLoop):
        asyncio.run(worker.run())
    assert sent == [ET.tostring(cot)]


def test_sensor_run_skips_none_cot(monkeypatch):
    worker = _sensor_worker()
    sent = []

    async def _put(event):
        sent.append(event)

    async def _position():
        return 0.0, 0.0, 0.0, "9", "9"

    worker.put_queue = _put
    monkeypatch.setattr(worker, "_get_position", _position)
    monkeypatch.setattr(classes.lincot, "gen_sensor_cot", lambda *a: None)
    monkeypatch.setattr(classes.asyncio, "sleep", _stop_sleep)
    with pytest.raises(_StopLoop):
        asyncio.run(worker.run())
    assert sent == []


@pytest.fixture
def fake_gpsd(monkeypatch):
    module = types.SimpleNamespace()
    monkeypatch.setattr(classes, "_gpsd", module)
    return module


def test_get_position_uses_gpsd_result(monkeypatch, fake_gpsd):
    worker = _sensor_worker()
    fix = (1.0, 2.0, 3.0, "4.0", "5.0")
    monkeypatch.setattr(classes.SensorWorker, "_poll_gpsd", staticmethod(lambda: fix))
    assert asyncio.run(worker._get_position()) == fix


def test_get_position_falls_back_when_gpsd_has_no_fix(monkeypatch, fake_gpsd):
    worker = _sensor_worker({"SENSOR_LAT": "10.5", "SENSOR_LON": "20.5"})
    monkeypatch.setattr(classes.SensorWorker, "_poll_gpsd", staticmethod(lambda: None))
    lat, lon, _hae, ce, le = asyncio.run(worker._get_position())
    assert (lat, lon) == (10.5, 20.5)
    assert ce == le == "9999999.0"


def test_get_position_falls_back_when_gpsd_raises(monkeypatch, fake_gpsd):
    worker = _sensor_worker({"STATIC_LAT": "7.0", "STATIC_LON": "8.0"})

    def _boom():
        raise ConnectionRefusedError("gpsd down")

    monkeypatch.setattr(classes.SensorWorker, "_poll_gpsd", staticmethod(_boom))
    lat, lon, _hae, ce, le = asyncio.run(worker._get_position())
    # No SENSOR_* position, so the static host position is used.
    assert (lat, lon) == (7.0, 8.0)
    assert ce == le == "9999999.0"


class _Packet:
    def __init__(self, mode=3, position=(1.0, 2.0), alt=30.0, error=None):
        self.mode = mode
        self._position = position
        self._alt = alt
        if error is not None:
            self.error = error

    def position(self):
        if isinstance(self._position, Exception):
            raise self._position
        return self._position

    def altitude(self):
        if isinstance(self._alt, Exception):
            raise self._alt
        return self._alt


def _serve(fake_gpsd, packet):
    connects = []
    fake_gpsd.connect = lambda: connects.append(True)
    fake_gpsd.get_current = lambda: packet
    return connects


def test_poll_gpsd_no_fix_returns_none(fake_gpsd):
    connects = _serve(fake_gpsd, _Packet(mode=1))
    assert classes.SensorWorker._poll_gpsd() is None
    assert connects == [True]


def test_poll_gpsd_position_error_returns_none(fake_gpsd):
    _serve(fake_gpsd, _Packet(position=RuntimeError("no fix")))
    assert classes.SensorWorker._poll_gpsd() is None


def test_poll_gpsd_altitude_error_uses_zero(fake_gpsd):
    _serve(fake_gpsd, _Packet(mode=2, alt=RuntimeError("2D only")))
    assert classes.SensorWorker._poll_gpsd() == (
        1.0, 2.0, 0.0, "9999999.0", "9999999.0"
    )


def test_poll_gpsd_reports_error_estimates(fake_gpsd):
    _serve(fake_gpsd, _Packet(error={"x": 3.2, "v": 5.1}))
    assert classes.SensorWorker._poll_gpsd() == (1.0, 2.0, 30.0, "3.2", "5.1")


def test_poll_gpsd_missing_error_attribute_uses_sentinel(fake_gpsd):
    packet = _Packet()
    assert not hasattr(packet, "error")
    _serve(fake_gpsd, packet)
    _lat, _lon, _hae, ce, le = classes.SensorWorker._poll_gpsd()
    assert ce == le == "9999999.0"
