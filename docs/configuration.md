# Configuration

LINCOT reads a `[lincot]` INI section or equivalent environment variables (PyTAK convention: ALL CAPS).

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
| `GPS_INFO_CMD` | `gpspipe --json -n 5` | Command to fetch TPV JSON |
| `POLL_INTERVAL` | `61` | Seconds between reports |

When both `STATIC_LAT` and `STATIC_LON` are set, static mode is used instead of gpsd.

## CoT

| Key | Default | Description |
|-----|---------|-------------|
| `COT_TYPE` | `a-f-G-E-S` | CoT event type |
| `COT_STALE` | `3600` | Stale time in seconds |

## Edge node metadata (remarks + link)

| Key | Default | Description |
|-----|---------|-------------|
| `COCKPIT_URL` | `http://{hostname}.local:9090/` | Cockpit URL in remarks and `<link>` |
| `SSH_USER` | `pi` | SSH user hint in remarks |
| `REMARKS_EXTRA` | — | Additional freeform remark text |
| `REMARKS_EXTRA_CMD` | — | Command to run for dynamic freeform remark text; stdout is appended |
| `REMARKS_EXTRA_CMD_TIMEOUT` | `2` | Seconds before the dynamic remarks command is abandoned |
| `COT_HOST_ID` | `lincot@{hostname}` | Source attribution in remarks |

## PyTAK transport / TLS

LINCOT uses PyTAK for networking. See the [PyTAK configuration guide](https://pytak.rtfd.io/en/latest/configuration/) for:

- `TAK_PROTO`, `DEBUG`, `PREF_PACKAGE`
- `PYTAK_TLS_CLIENT_CERT`, `PYTAK_TLS_CLIENT_KEY`, and related TLS options

See [example-config.ini](https://github.com/snstac/lincot/blob/main/example-config.ini) in the repository.
