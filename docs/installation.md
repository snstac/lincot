# Installation

## Debian / Ubuntu / Raspberry Pi

Install from the signed snstac apt repository (lincot packages are no longer
served from public GitHub releases):

```sh
sudo curl -fsSL -o /usr/share/keyrings/snstac.gpg https://snstac.github.io/packages/snstac.gpg
sudo curl -fsSL -o /etc/apt/sources.list.d/snstac.sources https://snstac.github.io/packages/snstac.sources
sudo apt update
sudo apt install lincot
```

Optional Cockpit configuration UI:

```sh
sudo apt install cockpit-lincot
```

### GPS (gpsd) mode

For live GNSS position via `gpspipe`:

```sh
sudo apt install -y gpsd gpsd-clients
```

## Red Hat / Fedora / CentOS Stream / Rocky / Alma

Install from the signed snstac yum/dnf repository:

```sh
sudo curl -fsSL -o /etc/yum.repos.d/snstac.repo https://snstac.github.io/packages/snstac.repo
sudo dnf install lincot
```

Optional Cockpit configuration UI:

```sh
sudo dnf install cockpit-lincot
```

## Python package (pip)

```sh
python3 -m pip install lincot
```

Requires Python 3.9+ and PyTAK 7.x.

## From source

The source repository is private (org members only). With access:

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
