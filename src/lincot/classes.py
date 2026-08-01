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

"""LINCOT Class Definitions."""

import asyncio
import json
import os
import xml.etree.ElementTree as ET
from typing import Optional

import pytak

import lincot
from lincot.position import merge_sky, static_position_configured, static_tpv

try:
    import gpsd as _gpsd
except ImportError:
    _gpsd = None


class _NoStatus:
    """Stand-in for pytak.StatusWriter on a pytak too old to have one.

    AryaOS boxes are updated as packages, so lincot can land on a host whose
    pytak predates StatusWriter (added in 7.4.0) -- 7.3.13 is still in the
    field. A hard reference would raise AttributeError at import and take the
    gateway down over its telemetry helper, which is exactly backwards: putting
    the host on the map is the job, reporting on it is not.

    Degrading here is safe because it is VISIBLE. With nothing writing
    /run/lincot/status.json, the Cockpit plugin reports "No status from this
    gateway ... may be running a pytak too old to report status" rather than
    rendering an empty feed as though the GPS were merely searching.
    """

    def count(self, *args, **kwargs) -> None:
        return None

    def record(self, *args, **kwargs) -> None:
        return None

    def set(self, *args, **kwargs) -> None:
        return None

    def write(self, *args, **kwargs) -> bool:
        return False


# Resolved at import so a missing StatusWriter is a startup-time decision
# rather than an AttributeError on the first fix.
_StatusWriter = getattr(pytak, "StatusWriter", None)


def make_status(app_name: str, version: str):
    """Return a status writer, or a no-op if this pytak has none."""
    if _StatusWriter is None:
        return _NoStatus()
    return _StatusWriter(app_name, version=version)


def _fix_kind(gps_info: dict) -> str:
    """gpsd TPV mode as the string the CoT __gps detail already uses."""
    return {2: "2D", 3: "3D"}.get(gps_info.get("mode"), "none")


class LincotWorker(pytak.QueueWorker):
    """Poll GPS or static position and emit CoT events."""

    # Resolved again in run(); defaulted here so handle_data() can report the
    # source even if it is driven directly (tests, or a future caller).
    _position_source = "gpsd"

    def __init__(self, queue, config):
        """Initialize this class."""
        super().__init__(queue, config)
        if static_position_configured(config):
            self._position_source = "static"

        # Runtime status for Cockpit. Systemd gives us /run/lincot via
        # RuntimeDirectory=, so this lands where the plugin looks for it.
        #
        # LincotWorker owns the file, not SensorWorker: two workers writing one
        # path would clobber each other, and this is the worker whose silence
        # actually means something is wrong.
        self.status = make_status("lincot", lincot.__version__)

    async def handle_data(self, data) -> None:
        """Handle received GPS Info data."""
        if not data:
            # Nothing was read. Deliberately NOT counted as received, so a
            # receiver producing nothing cannot be mistaken for one with a fix.
            return

        self.status.count("rx")

        event: Optional[bytes] = lincot.position_to_cot(data, self.config)

        # Record EVERY poll, not only the ones that place the host. A GPS that
        # is powered and searching still proves the chain works; a feed showing
        # only successful fixes would sit empty on a box that is merely indoors,
        # which reads as a fault. The `placed` flag keeps the two distinct.
        self.status.record(
            fix=_fix_kind(data),
            lat=data.get("lat"),
            lon=data.get("lon"),
            alt=data.get("altHAE") or data.get("altMSL"),
            speed=data.get("speed"),
            track=data.get("track"),
            sats_used=data.get("uSat"),
            sats_seen=data.get("nSat"),
            hdop=data.get("hdop"),
            source=self._position_source,
            placed=event is not None,
        )

        if event:
            self.status.count("emitted")
            self.status.write()
            await self.put_queue(event)
            return

        # The common indoor case: a TPV with mode 0/1 carries no lat/lon.
        self.status.count("no_fix")
        self.status.write()

    async def get_gps_info(self) -> None:
        """Get GPS Info data via gpspipe (or GPS_INFO_CMD)."""
        gpspipe_data: Optional[str] = None
        gps_data: Optional[str] = None
        try:
            with os.popen(self.gps_info_cmd) as gps_info_cmd:
                gpspipe_data = gps_info_cmd.read()
        except OSError as exc:
            self._logger.warning("GPS command failed: %s", exc)
            # Each failure mode gets its own counter: "gpspipe will not run" and
            # "gpsd answers but has no fix" need different fixes, and a single
            # error count would not tell an operator which one they have.
            self.status.count("gps_cmd_failed")
            self.status.write()
            return

        if not gpspipe_data:
            self._logger.debug("No output from %s", self.gps_info_cmd)
            self.status.count("gps_no_output")
            self.status.write()
            return

        sky_lines: list = []
        for line in gpspipe_data.split("\n"):
            if "TPV" in line:
                gps_data = line
            elif "SKY" in line:
                sky_lines.append(line)

        if not gps_data:
            self._logger.debug("No TPV record in gpspipe output")
            self.status.count("no_tpv")
            self.status.write()
            return

        self._logger.debug("GPS_INFO=%s", gps_data)
        try:
            gps_info = json.loads(gps_data)
        except json.JSONDecodeError as exc:
            self._logger.warning("Invalid GPS JSON: %s", exc)
            self.status.count("bad_json")
            self.status.write()
            return

        merge_sky(gps_info, sky_lines)
        await self.handle_data(gps_info)

    async def run(self, number_of_iterations=-1) -> None:
        """Run worker loop: read position and output CoT."""
        cot_url: str = self.config.get("COT_URL")
        if not cot_url:
            self._logger.error("COT_URL not set, exiting.")
            return
        self._logger.info("Sending to: %s", cot_url)

        poll_interval: int = int(
            self.config.get("POLL_INTERVAL", lincot.DEFAULT_POLL_INTERVAL)
        )
        self.gps_info_cmd = self.config.get("GPS_INFO_CMD", lincot.DEFAULT_GPS_INFO_CMD)
        use_static = static_position_configured(self.config)
        self._position_source = "static" if use_static else "gpsd"

        # Write immediately, before the first poll. POLL_INTERVAL defaults to 61
        # seconds, so without this the management UI would report "no status
        # from this gateway" -- indistinguishable from a gateway that failed to
        # start -- for a full minute after every restart.
        self.status.set(
            source=self._position_source,
            poll_interval_s=poll_interval,
        )
        self.status.write(force=True)

        heartbeat = asyncio.ensure_future(self._heartbeat())
        try:
            while True:
                if use_static:
                    self._logger.info(
                        "Sending static position to %s every %s seconds.",
                        cot_url,
                        poll_interval,
                    )
                    tpv = static_tpv(self.config)
                    if tpv:
                        await self.handle_data(tpv)
                else:
                    self._logger.info(
                        "Sending position from %s to %s every %s seconds.",
                        self.gps_info_cmd,
                        cot_url,
                        poll_interval,
                    )
                    await self.get_gps_info()

                await asyncio.sleep(poll_interval)
        finally:
            heartbeat.cancel()

    async def _heartbeat(self, interval: float = 5.0) -> None:
        """Keep the status file fresh between polls.

        The UI decides liveness from whether this file keeps changing. Writing
        only on a successful fix would make a 61-second poll interval -- or a
        GPS that is simply searching -- look like a wedged service.
        """
        while True:
            await asyncio.sleep(interval)
            self.status.write(force=True)


class SensorWorker(pytak.QueueWorker):
    """Periodic sensor CoT heartbeat. Sources position from gpsd, config, or null island."""

    async def run(self, _=-1) -> None:
        """Run worker loop: emit sensor beacon CoT at configured interval."""
        period = int(self.config.get(
            "SENSOR_KEEPALIVE_PERIOD", lincot.DEFAULT_SENSOR_KEEPALIVE_PERIOD))
        self._logger.info(
            "Running SensorWorker (period=%ds, gpsd=%s)", period, _gpsd is not None)
        while True:
            lat, lon, hae, ce, le = await self._get_position()
            cot = lincot.gen_sensor_cot(self.config, lat, lon, hae, ce, le)
            if cot is not None:
                await self.put_queue(ET.tostring(cot))
            await asyncio.sleep(period)

    async def _get_position(self):
        """Resolve sensor position: gpsd → static config → null island."""
        if _gpsd is not None:
            try:
                result = await asyncio.to_thread(self._poll_gpsd)
                if result is not None:
                    return result
            except Exception as exc:
                self._logger.debug("gpsd unavailable: %s", exc)
        lat = float(self.config.get("SENSOR_LAT") or lincot.DEFAULT_SENSOR_LAT)
        lon = float(self.config.get("SENSOR_LON") or lincot.DEFAULT_SENSOR_LON)
        hae = float(self.config.get("SENSOR_HAE") or lincot.DEFAULT_SENSOR_HAE)
        return lat, lon, hae, "9999999.0", "9999999.0"

    @staticmethod
    def _poll_gpsd():
        """Poll gpsd for current position. Returns None if fix is unavailable."""
        _gpsd.connect()
        packet = _gpsd.get_current()
        if packet.mode < 2:
            return None
        try:
            lat, lon = packet.position()
        except Exception:
            return None
        try:
            hae = packet.altitude()
        except Exception:
            hae = 0.0
        ce = str(getattr(packet, "error", {}).get("x", "9999999.0") or "9999999.0")
        le = str(getattr(packet, "error", {}).get("v", "9999999.0") or "9999999.0")
        return lat, lon, hae, ce, le
