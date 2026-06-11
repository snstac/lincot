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
from lincot.position import static_position_configured, static_tpv

try:
    import gpsd as _gpsd
except ImportError:
    _gpsd = None


class LincotWorker(pytak.QueueWorker):
    """Poll GPS or static position and emit CoT events."""

    async def handle_data(self, data) -> None:
        """Handle received GPS Info data."""
        event: Optional[bytes] = lincot.position_to_cot(data, self.config)
        if event:
            await self.put_queue(event)

    async def get_gps_info(self) -> None:
        """Get GPS Info data via gpspipe (or GPS_INFO_CMD)."""
        gpspipe_data: Optional[str] = None
        gps_data: Optional[str] = None
        try:
            with os.popen(self.gps_info_cmd) as gps_info_cmd:
                gpspipe_data = gps_info_cmd.read()
        except OSError as exc:
            self._logger.warning("GPS command failed: %s", exc)
            return

        if not gpspipe_data:
            self._logger.debug("No output from %s", self.gps_info_cmd)
            return

        for line in gpspipe_data.split("\n"):
            if "TPV" in line:
                gps_data = line

        if not gps_data:
            self._logger.debug("No TPV record in gpspipe output")
            return

        self._logger.debug("GPS_INFO=%s", gps_data)
        try:
            gps_info = json.loads(gps_data)
        except json.JSONDecodeError as exc:
            self._logger.warning("Invalid GPS JSON: %s", exc)
            return
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
