## Unreleased

- Empty or invalid numeric settings (`POLL_INTERVAL`, `GPS_INFO_TIMEOUT`,
  `SENSOR_KEEPALIVE_PERIOD`, `COT_STALE`, `SENSOR_LAT/LON/HAE`) now fall back
  to their defaults with a logged warning instead of crashing a worker. Values
  below 1 for `POLL_INTERVAL`/`SENSOR_KEEPALIVE_PERIOD`/`COT_STALE` are ignored
  (so `COT_STALE=0` now means the 3600 s default, not an immediately stale
  receiver beacon).
- Invalid `STATIC_LAT`/`STATIC_LON` (not a number, NaN/inf, or out of range) no
  longer crash or mis-place the position loop; the gateway reports
  `bad_static_position` and a degraded health message.
- The receiver beacon (`SensorWorker`) uses `STATIC_LAT`/`STATIC_LON`/`STATIC_HAE`
  when gpsd has no fix and no `SENSOR_LAT`/`SENSOR_LON` is set, instead of
  placing the receiver marker at null island.
- An altitude of exactly `0.0` is reported as `0.0` rather than replaced by
  `altMSL` or "unknown".
- GPS remarks no longer print `8/None sats` when gpsd reports satellites used
  but not seen.
- Empty `SENSOR_ID`/`SENSOR_CALLSIGN`/`SENSOR_COT_TYPE`/`SENSOR_PAYLOAD_TYPE`
  use the defaults instead of producing a `SENSOR.` uid.
- `python -m lincot.commands` loads the `lincot` app instead of `__main__`.
- Docs: `GPS_INFO_CMD` default is `gpspipe --json -n 12` (example configs said
  `-n 5`, which drops satellite counts); document `GPS_INFO_TIMEOUT`, the
  receiver beacon settings, runtime status and the release process.

## LinCoT 1.3.9

- Add `SENSOR_BEACON=0` to disable the separate receiver marker without
  disabling the main host beacon.

## LinCoT 1.3.8

- Report the common gateway health contract (`health`, `input`, `output`) in
  the runtime status file. Require `pytak >= 7.5.0`.

## LinCoT 1.3.7

- Run `GPS_INFO_CMD` as an asyncio subprocess bounded by `GPS_INFO_TIMEOUT`
  (default 15 s), killing the whole process group on timeout, so an absent
  receiver can no longer block every coroutine.

## LinCoT 1.3.6

- Write runtime status to `/run/lincot/status.json` (counters, recent fixes,
  position source) for the Cockpit plugin, with a 5 s heartbeat. Degrades to a
  no-op on a pytak without `StatusWriter`.

## LinCoT 1.3.5

- Merge every gpsd SKY report so satellite counts are not lost when the last
  SKY is DOP-only; default `GPS_INFO_CMD` reads 12 records.

## LinCoT 1.3.4

- Add `<precisionlocation>` and `<__gps>` detail (fix, satellites, HDOP, speed,
  altitude) and a GPS-quality remarks line to the position CoT.

## LinCoT 1.3.3

- Add `COT_DETAIL_XML_CMD` support for structured CoT detail children on host
  beacons. Command output is parsed as XML and ignored if invalid, preserving
  normal beacon generation.

## LinCoT 1.3.2

- Use PyTAK's shared CoT helpers for point formatting, event/detail construction,
  XML serialization, and credential-safe TAK URL display.
- Require `pytak >= 7.3.12`.

## LinCoT 1.3.1

- Add dynamic `REMARKS_EXTRA_CMD` support for host-generated CoT remarks.
- Populate CoT point `ce` and `le` from gpsd TPV accuracy fields.
- Recommend `python3-gps` in Debian packages for gpsd-backed sensor position.

## LinCoT 1.3.0

- Add `SensorWorker`: periodic `a-f-G-E-S-E` sensor CoT heartbeat every `SENSOR_KEEPALIVE_PERIOD` seconds (default 30).
- Position sourced from system gpsd → static `SENSOR_LAT`/`SENSOR_LON`/`SENSOR_HAE` config → null island fallback.
- Add `gen_sensor_cot()`: reusable CoT builder for sensor beacon events.
- New constants: `DEFAULT_SENSOR_KEEPALIVE_PERIOD=30`, `DEFAULT_SENSOR_LAT/LON/HAE=0.0`.

# LINCOT 1.2.3
# -----------
#
# - Default Cockpit URL uses default-route or WiFi interface IP, not localhost

# LINCOT 1.2.2
# -----------
#
# - Limit CoT lat/lon output to four decimal places

# LINCOT 1.2.1
# -----------
#
# - Fix missing VERSION file in Debian/PyPI installs (service crash on import)
# - Add cryptography to CI test requirements (PyTAK import chain)

# LINCOT 1.2.0
# -----------
#
# - Hostname default callsign; machine-id default CoT uid
# - Static position mode (STATIC_LAT/LON) or gpsd via gpspipe
# - CoT remarks with Cockpit/SSH/TAK connect info; link to Cockpit URL
# - PyTAK 7.x; src/ package layout; MkDocs documentation
# - cockpit-lincot Cockpit configuration plugin (separate package)

LINCOT 1.0.0
--------------
Initial release.
