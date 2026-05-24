# Quick Start

Get a Linux edge node position onto the TAK network in a few minutes.

## 1. Install LINCOT

=== "pip"

    ```sh
    python3 -m pip install lincot
    ```

=== "Debian / Ubuntu"

    ```sh
  wget https://github.com/snstac/lincot/releases/latest/download/python3-lincot_latest_all.deb
  sudo apt install -f ./python3-lincot_latest_all.deb
    ```

See [Installation](installation.md) for PyTAK dependency details.

## 2. Configure

Create `config.ini`:

```ini
[lincot]
COT_URL = udp://239.2.3.1:6969
```

For a fixed site without GPS:

```ini
[lincot]
COT_URL = udp://239.2.3.1:6969
STATIC_LAT = 45.0
STATIC_LON = -122.0
```

## 3. Run

```sh
lincot -c config.ini
```

On Debian systems with the package installed:

```sh
sudo systemctl enable --now lincot
```

Configure via `/etc/default/lincot` or the optional **cockpit-lincot** Cockpit plugin.
