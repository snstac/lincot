# Troubleshooting

## `COT_URL not set, exiting`

Set `COT_URL` in your config file or environment (`/etc/default/lincot` on Debian).

## No position from gpsd

- Confirm gpsd is running: `systemctl status gpsd`
- Test manually: `gpspipe --json -n 5 | grep TPV`
- Install clients: `sudo apt install gpsd-clients`
- Or use static mode with `STATIC_LAT` and `STATIC_LON`

## Is it running? Runtime status

The service writes `/run/lincot/status.json` every few seconds (read by the
Cockpit plugin). Its counters tell failure modes apart:

| Counter | Meaning |
|---------|---------|
| `rx` | TPV reports handled |
| `emitted` | Position CoT events sent |
| `no_fix` | gpsd answered but the receiver has no fix (common indoors) |
| `gps_cmd_failed` | `GPS_INFO_CMD` would not run |
| `gps_cmd_timeout` | `GPS_INFO_CMD` exceeded `GPS_INFO_TIMEOUT` |
| `gps_no_output` | Command ran but printed nothing |
| `no_tpv` | Output had SKY but no TPV |
| `bad_json` | Output was not JSON |
| `bad_static_position` | `STATIC_LAT`/`STATIC_LON` are not numbers |

No status file at all usually means an old pytak without `StatusWriter`
(before 7.4.0) or the service is not running.

## "Ignoring invalid ..." in the log

A numeric setting was empty or not a number and the default was used. Fix the
value in `/etc/default/lincot` or the config file.

## Receiver marker at 0, 0 (null island)

The receiver beacon had no gpsd fix and no `SENSOR_LAT`/`SENSOR_LON` or
`STATIC_LAT`/`STATIC_LON`. Set one of them, install `gpsd-py3`
(`python3 -m pip install gpsd-py3`; Debian's `python3-gps` is a different
module), or disable
it with `SENSOR_BEACON=0`.

## Satellite counts missing from CoT

Make sure `GPS_INFO_CMD` reads enough records (the default `gpspipe --json -n 12`).
Older configs with `-n 5` often miss the full SKY report.

## TLS / TAK Server connection errors

See [PyTAK troubleshooting](https://pytak.rtfd.io/en/latest/troubleshooting/) for certificate and enrollment issues.

## Duplicate markers after upgrade

LINCOT 1.2.0 changes default UID (machine-id) and callsign (hostname). Existing map icons from older MAC-based UIDs will remain until they stale out.
