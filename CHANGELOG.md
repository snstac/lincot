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
