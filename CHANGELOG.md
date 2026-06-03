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
