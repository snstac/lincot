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

"""Tests for the runtime status surface LincotWorker writes for Cockpit.

These drive the coroutines with ``asyncio.run()`` rather than declaring bare
``async def`` tests. That is not a style choice: pytest-asyncio is not installed
in the build/CI environment for this package, and pytest SKIPS bare async tests
while still reporting the run as passed -- i.e. tests that cannot fail. Calling
asyncio.run() explicitly keeps them real regardless of plugins.
"""

import asyncio
import json
import logging
import os

import pytest

import pytak

from lincot import classes


needs_statuswriter = pytest.mark.skipif(
    not hasattr(pytak, "StatusWriter"),
    reason="installed pytak has no StatusWriter (pre-7.4.0)",
)


# A real gpsd TPV with a 3D fix, as gpspipe -w -n emits it.
TPV_3D = {
    "class": "TPV",
    "device": "/dev/ttyACM0",
    "mode": 3,
    "lat": 37.7648,
    "lon": -122.4187,
    "altHAE": 42.5,
    "speed": 0.31,
    "track": 187.4,
    "eph": 8.2,
    "epv": 14.0,
    "uSat": 9,
    "nSat": 14,
    "hdop": 0.94,
}

# gpsd reports TPVs while the receiver is still searching: mode 1, no position.
TPV_NO_FIX = {
    "class": "TPV",
    "device": "/dev/ttyACM0",
    "mode": 1,
}


async def _noop_put(event):
    return None


def _worker(tmp_path, source="gpsd", put=None):
    worker = classes.LincotWorker.__new__(classes.LincotWorker)
    worker.config = {}
    worker._logger = logging.getLogger("test")
    worker._position_source = source
    worker.status = pytak.StatusWriter(
        "lincot-test", path=str(tmp_path / "status.json")
    )
    worker.put_queue = put or _noop_put
    return worker


def _doc(worker):
    with open(worker.status.path) as handle:
        return json.load(handle)


@needs_statuswriter
class TestStatusSurface:
    """What the Cockpit plugin reads out of /run/lincot/status.json.

    A lincot that is working and one that is wedged look identical from
    outside, and both emit nothing when the GPS has no fix. These assert
    against real gpsd TPV documents rather than restating the code's shape.
    """

    def test_fix_is_emitted_and_appears_in_the_feed(self, tmp_path):
        sent = []

        async def _put(event):
            sent.append(event)

        worker = _worker(tmp_path, put=_put)
        asyncio.run(worker.handle_data(dict(TPV_3D)))

        doc = _doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["emitted"] == 1
        assert sent, "a 3D fix must still reach the TX queue"

        entry = doc["recent"][-1]
        assert entry["fix"] == "3D"
        assert entry["lat"] == pytest.approx(37.7648)
        assert entry["sats_used"] == 9
        assert entry["sats_seen"] == 14
        assert entry["hdop"] == pytest.approx(0.94)
        assert entry["source"] == "gpsd"
        assert entry["placed"] is True

    def test_searching_receiver_is_visible_rather_than_silent(self, tmp_path):
        """A powered GPS with no fix is the common indoor case, not an error.

        It emits no CoT, so before this surface it left no trace at all --
        identical to a dead antenna or a stopped gpsd.
        """
        worker = _worker(tmp_path)
        asyncio.run(worker.handle_data(dict(TPV_NO_FIX)))

        doc = _doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["no_fix"] == 1
        assert "emitted" not in doc["counters"]

        entry = doc["recent"][-1]
        assert entry["fix"] == "none"
        assert entry["placed"] is False
        assert entry["lat"] is None

    def test_static_position_is_labelled_as_such(self, tmp_path):
        """An operator must be able to tell a configured position from a fix."""
        worker = _worker(tmp_path, source="static")
        asyncio.run(
            worker.handle_data(
                {"class": "TPV", "lat": 1.0, "lon": 2.0, "altHAE": "9999999.0"}
            )
        )

        entry = _doc(worker)["recent"][-1]
        assert entry["source"] == "static"
        assert entry["placed"] is True
        # No gpsd mode key on a static TPV: reported honestly as no fix.
        assert entry["fix"] == "none"

    def test_empty_poll_is_not_counted_as_received(self, tmp_path):
        """Reading nothing is not a position report."""
        worker = _worker(tmp_path)
        asyncio.run(worker.handle_data(None))
        asyncio.run(worker.handle_data({}))
        assert not os.path.exists(worker.status.path)

    def test_gps_command_failure_has_its_own_counter(self, tmp_path, monkeypatch):
        """'gpspipe will not run' and 'gpsd has no fix' need different fixes.

        A single error count would not tell an operator which one they have.
        """
        worker = _worker(tmp_path)
        worker.gps_info_cmd = "does-not-matter"

        def _boom(_cmd):
            raise OSError("no such file")

        monkeypatch.setattr(classes.os, "popen", _boom)
        asyncio.run(worker.get_gps_info())

        doc = _doc(worker)
        assert doc["counters"]["gps_cmd_failed"] == 1
        assert "rx" not in doc["counters"]

    def test_unparseable_gps_json_is_counted_but_not_as_a_fix(
        self, tmp_path, monkeypatch
    ):
        worker = _worker(tmp_path)
        worker.gps_info_cmd = "does-not-matter"

        class _FakePipe:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return '{"class":"TPV" this is not json\n'

        monkeypatch.setattr(classes.os, "popen", lambda _cmd: _FakePipe())
        asyncio.run(worker.get_gps_info())

        doc = _doc(worker)
        assert doc["counters"]["bad_json"] == 1
        assert "rx" not in doc["counters"]

    def test_output_with_no_tpv_is_counted_separately(self, tmp_path, monkeypatch):
        """gpsd answering with only SKY means a receiver seen but not fixed."""
        worker = _worker(tmp_path)
        worker.gps_info_cmd = "does-not-matter"

        class _FakePipe:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return '{"class":"SKY","hdop":1.2}\n'

        monkeypatch.setattr(classes.os, "popen", lambda _cmd: _FakePipe())
        asyncio.run(worker.get_gps_info())

        doc = _doc(worker)
        assert doc["counters"]["no_tpv"] == 1
        assert "rx" not in doc["counters"]

    def test_rate_limiting_means_the_file_can_lag_briefly(self, tmp_path):
        """Documents the 1/sec floor so nobody 'fixes' it into a write per poll."""
        worker = _worker(tmp_path)
        asyncio.run(worker.handle_data(dict(TPV_NO_FIX)))
        asyncio.run(worker.handle_data(dict(TPV_3D)))

        # Second write was suppressed by the rate limiter; the heartbeat is what
        # reconciles it in the running gateway.
        assert _doc(worker)["counters"]["rx"] == 1
        worker.status.write(force=True)
        assert _doc(worker)["counters"]["rx"] == 2


@needs_statuswriter
class TestStatusHeartbeat:
    """POLL_INTERVAL defaults to 61s; the UI must not read that as wedged."""

    def test_heartbeat_writes_with_no_traffic_at_all(self, tmp_path):
        worker = classes.LincotWorker.__new__(classes.LincotWorker)
        worker._logger = logging.getLogger("test")
        worker.status = pytak.StatusWriter(
            "lincot-test", path=str(tmp_path / "status.json")
        )

        async def _drive():
            task = asyncio.ensure_future(worker._heartbeat(interval=0.01))
            await asyncio.sleep(0.05)
            task.cancel()

        asyncio.run(_drive())

        doc = _doc(worker)
        assert doc["counters"] == {}
        assert doc["wall_t"] > 0


class TestStatusDegradesVisibly:
    """A pytak without StatusWriter must not take the gateway down.

    Fleet boxes run pytak 7.3.13, which has no StatusWriter at all.
    """

    def test_no_op_status_when_pytak_is_too_old(self, monkeypatch):
        monkeypatch.setattr(classes, "_StatusWriter", None)
        status = classes.make_status("lincot", "0.1.0")

        # Every call LincotWorker makes must be safe on the stand-in.
        status.count("rx")
        status.count("emitted", 2)
        status.record(fix="3D", placed=True)
        status.set(source="gpsd")
        assert status.write() is False
        assert status.write(force=True) is False

    def test_worker_still_emits_with_no_statuswriter(self, monkeypatch):
        """The whole point: no StatusWriter must not break the data path."""
        monkeypatch.setattr(classes, "_StatusWriter", None)
        monkeypatch.setattr(
            classes.lincot, "position_to_cot", lambda data, config: b"<event/>"
        )

        worker = classes.LincotWorker.__new__(classes.LincotWorker)
        worker.config = {}
        worker._logger = logging.getLogger("test")
        worker._position_source = "gpsd"
        worker.status = classes.make_status("lincot", "0.1.0")

        sent = []

        async def _put(event):
            sent.append(event)

        worker.put_queue = _put
        asyncio.run(worker.handle_data(dict(TPV_3D)))

        assert isinstance(worker.status, classes._NoStatus)
        assert sent == [b"<event/>"]

    def test_real_writer_used_when_available(self):
        if classes._StatusWriter is None:
            pytest.skip("installed pytak has no StatusWriter")
        assert not isinstance(classes.make_status("x", "0"), classes._NoStatus)


def test_fix_kind_maps_gpsd_modes():
    """Mode 0/1 are 'searching', not a fix; 2/3 are real."""
    assert classes._fix_kind({"mode": 3}) == "3D"
    assert classes._fix_kind({"mode": 2}) == "2D"
    assert classes._fix_kind({"mode": 1}) == "none"
    assert classes._fix_kind({}) == "none"
