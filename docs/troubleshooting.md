# Troubleshooting

## `COT_URL not set, exiting`

Set `COT_URL` in your config file or environment (`/etc/default/lincot` on Debian).

## No position from gpsd

- Confirm gpsd is running: `systemctl status gpsd`
- Test manually: `gpspipe --json -n 5 | grep TPV`
- Install clients: `sudo apt install gpsd-clients`
- Or use static mode with `STATIC_LAT` and `STATIC_LON`

## TLS / TAK Server connection errors

See [PyTAK troubleshooting](https://pytak.rtfd.io/en/latest/troubleshooting/) for certificate and enrollment issues.

## Duplicate markers after upgrade

LINCOT 1.2.0 changes default UID (machine-id) and callsign (hostname). Existing map icons from older MAC-based UIDs will remain until they stale out.
