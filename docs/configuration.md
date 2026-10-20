# Configuration

LINCOT reads a `[lincot]` INI section or equivalent environment variables (PyTAK convention: ALL CAPS).

`POLL_INTERVAL`, `GPS_INFO_TIMEOUT`, `COT_STALE`, `SENSOR_KEEPALIVE_PERIOD` and
`SENSOR_LAT`/`SENSOR_LON`/`SENSOR_HAE` fall back to the default shown below,
with a logged warning, when they are empty or not a number (for example
`POLL_INTERVAL=` left blank in `/etc/default/lincot`); they do not stop the
service. `STATIC_LAT`/`STATIC_LON` that are not valid coordinates disable
static mode output and are reported as `bad_static_position`.

## Required

| Key | Description |
|-----|-------------|
| `COT_URL` | CoT destination URL (`udp://`, `tcp://`, `tls://`, etc.) |

## Identity

| Key | Default | Description |
|-----|---------|-------------|
| `CALLSIGN` | hostname | Marker callsign |
| `COT_UID` | `/etc/machine-id` | Stable CoT event UID |

## Position

| Key | Default | Description |
|-----|---------|-------------|
| `STATIC_LAT` | — | Fixed latitude (requires `STATIC_LON`) |
| `STATIC_LON` | — | Fixed longitude (requires `STATIC_LAT`) |
| `STATIC_HAE` | unknown | Optional altitude |
| `STATIC_COURSE` | `0.0` | Optional track course |
| `STATIC_SPEED` | `0.0` | Optional track speed (m/s) |
| `GPS_INFO_CMD` | `gpspipe --json -n 12` | Command to fetch TPV + SKY JSON. Keep at least ~12 records: gpsd interleaves DOP-only SKY reports, and fewer records usually miss the satellite counts |
| `GPS_INFO_TIMEOUT` | `15` | Seconds before `GPS_INFO_CMD` is killed (counted as `gps_cmd_timeout`) |
| `POLL_INTERVAL` | `61` | Seconds between reports (minimum 1) |

When both `STATIC_LAT` and `STATIC_LON` are set, static mode is used instead of gpsd.

## CoT

| Key | Default | Description |
|-----|---------|-------------|
| `COT_TYPE` | `a-f-G-E-S` | CoT event type |
| `COT_STALE` | `3600` | Stale time in seconds |

## Receiver beacon

A second, periodic `a-f-G-E-S-E` marker for the GPS receiver itself, sent by
`SensorWorker`. Its position comes from gpsd (via the `gpsd-py3` Python package,
which provides `import gpsd`), then `SENSOR_LAT`/`SENSOR_LON`, then `STATIC_LAT`/`STATIC_LON`,
then `0, 0`.

| Key | Default | Description |
|-----|---------|-------------|
| `SENSOR_BEACON` | `1` | Set `0` (or `false`/`no`/`off`) to disable the receiver marker |
| `SENSOR_KEEPALIVE_PERIOD` | `30` | Seconds between receiver beacons (minimum 1) |
| `SENSOR_ID` | `lincot_{hostname}` | Sensor id; CoT uid is `SENSOR.{SENSOR_ID}` |
| `SENSOR_CALLSIGN` | `SENSOR_ID` | Receiver marker callsign |
| `SENSOR_COT_TYPE` | `a-f-G-E-S-E` | Receiver marker CoT type |
| `SENSOR_PAYLOAD_TYPE` | `GPS-Receiver` | `<sensor type>` attribute |
| `SENSOR_LAT` / `SENSOR_LON` / `SENSOR_HAE` | — | Receiver position when gpsd has no fix |

## Edge node metadata (remarks + link)

| Key | Default | Description |
|-----|---------|-------------|
| `COCKPIT_URL` | `http://{host-ip}:9090/` | Cockpit URL in remarks and `<link>`. Defaults to the default-route (then `wifi0`/`wlan0`) IPv4 address, else `{hostname}.local`. A `localhost` override is rewritten to that address |
| `SSH_USER` | `pi` | SSH user hint in remarks |
| `REMARKS_EXTRA` | — | Additional freeform remark text |
| `REMARKS_EXTRA_CMD` | — | Command to run for dynamic freeform remark text; stdout is appended |
| `REMARKS_EXTRA_CMD_TIMEOUT` | `2` | Seconds before the dynamic remarks command is abandoned |
| `COT_DETAIL_XML_CMD` | — | Command to run for structured CoT detail XML children; stdout is parsed and appended to `<detail>` |
| `COT_DETAIL_XML_CMD_TIMEOUT` | `2` | Seconds before the dynamic detail command is abandoned |
| `COT_HOST_ID` | `lincot@{hostname}` | Source attribution in remarks |

## PyTAK transport / TLS

LINCOT uses PyTAK for networking. See the [PyTAK configuration guide](https://pytak.rtfd.io/en/latest/configuration/) for:

- `TAK_PROTO`, `DEBUG`, `PREF_PACKAGE`
- `PYTAK_TLS_CLIENT_CERT`, `PYTAK_TLS_CLIENT_KEY`, and related TLS options

See [example-config.ini](https://github.com/snstac/lincot/blob/main/example-config.ini) in the repository.
