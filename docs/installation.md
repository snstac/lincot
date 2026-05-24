# Installation

## Debian / Ubuntu / Raspberry Pi

```sh
wget https://github.com/snstac/pytak/releases/latest/download/pytak_latest_all.deb
sudo apt install -f ./pytak_latest_all.deb
wget https://github.com/snstac/lincot/releases/latest/download/python3-lincot_latest_all.deb
sudo apt install -f ./python3-lincot_latest_all.deb
```

Optional Cockpit configuration UI:

```sh
wget https://github.com/snstac/cockpit-lincot/releases/latest/download/cockpit-lincot_latest_all.deb
sudo apt install -f ./cockpit-lincot_latest_all.deb
```

### GPS (gpsd) mode

For live GNSS position via `gpspipe`:

```sh
sudo apt install -y gpsd gpsd-clients
```

## Python package (pip)

```sh
python3 -m pip install lincot
```

Requires Python 3.9+ and PyTAK 7.x.

## From source

```sh
git clone https://github.com/snstac/lincot.git
cd lincot
python3 -m pip install -e .
```

## systemd

The Debian package installs `lincot.service`. Configure environment in `/etc/default/lincot`, then:

```sh
sudo systemctl restart lincot
sudo journalctl -fu lincot
```
