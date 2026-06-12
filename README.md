<img src="docs/media/lincot_logo.svg" alt="LINCOT Logo" width="200">

# LINCOT — Linux GPS to TAK Gateway

LINCOT reports a Linux edge node's position to the [Team Awareness Kit (TAK)](https://tak.gov) ecosystem as Cursor on Target (CoT). It is built on [PyTAK](https://github.com/snstac/pytak) and supports live GNSS via `gpsd`/`gpspipe` or a configured static coordinate.

## Install

```sh
python3 -m pip install lincot
```

Debian package (includes systemd unit):

```sh
wget https://github.com/snstac/pytak/releases/latest/download/pytak_latest_all.deb
sudo apt install -f ./pytak_latest_all.deb
wget https://github.com/snstac/lincot/releases/latest/download/python3-lincot_latest_all.deb
sudo apt install -f ./python3-lincot_latest_all.deb
```

## Quick example

`config.ini`:

```ini
[lincot]
COT_URL = udp://239.2.3.1:6969
```

Run:

```sh
lincot -c config.ini
```

Fixed position (no GPS):

```ini
[lincot]
COT_URL = udp://239.2.3.1:6969
STATIC_LAT = 45.0
STATIC_LON = -122.0
```

## Features

- **Identity:** callsign defaults to hostname; CoT UID defaults to `/etc/machine-id`
- **Position:** gpsd (`gpspipe --json`) or static lat/lon
- **CoT detail:** remarks with Cockpit/SSH/TAK connect info; `<link>` to Cockpit URL
- **PyTAK transports:** UDP multicast, TCP, TLS, data packages, and more
- **Cockpit UI:** optional [cockpit-lincot](https://github.com/snstac/cockpit-lincot) plugin for `/etc/default/lincot`

## Documentation

Full documentation at **[lincot.rtfd.io](https://lincot.rtfd.io/)** including installation, configuration, and troubleshooting.

## The snstac TAK sensor ecosystem

Different sensor, same workflow — pick the gateway for your application; most have a
matching Cockpit plugin for browser-based management:

| Application | Gateway | Cockpit plugin |
|---|---|---|
| Aircraft via ADS-B (1090 MHz / 978 MHz UAT) | [adsbcot](https://github.com/snstac/adsbcot) | [cockpit-adsbcot](https://github.com/snstac/cockpit-adsbcot) |
| Ships & vessels via AIS | [aiscot](https://github.com/snstac/aiscot) | [cockpit-aiscot](https://github.com/snstac/cockpit-aiscot), [cockpit-aiscatcher](https://github.com/snstac/cockpit-aiscatcher) |
| Drone / UAS Remote ID (counter-UAS) | [dronecot](https://github.com/snstac/dronecot) | [cockpit-dronecot](https://github.com/snstac/cockpit-dronecot) |
| Own position via GPS/GNSS | [lincot](https://github.com/snstac/lincot) | [cockpit-lincot](https://github.com/snstac/cockpit-lincot), [cockpit-gps](https://github.com/snstac/cockpit-gps) |
| Radio direction finding (KrakenSDR) | [kraktak](https://github.com/snstac/kraktak) | — |
| APRS amateur radio | [aprscot](https://github.com/snstac/aprscot) | — |
| Weather stations | [windtak](https://github.com/snstac/windtak) | — |
| CoT routing / TAK Server bridging | [charontak](https://github.com/snstac/charontak) | — |

All gateways are built on [PyTAK](https://github.com/snstac/pytak), speak
**Cursor on Target (CoT)** to **ATAK, WinTAK, iTAK, TAK Server, and Mesh SA**, ship as
signed Debian/RPM packages at [snstac.github.io/packages](https://snstac.github.io/packages),
and come pre-installed on [AryaOS](https://github.com/snstac/aryaos), the
situational-awareness OS for Raspberry Pi.


## License & Copyright

Copyright Sensors & Signals LLC https://www.snstac.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
