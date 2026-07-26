"""Tests for merging gpsd SKY reports into the TPV.

Regression from the field: gpsd interleaves DOP-only SKY records with full-sky
ones (on a u-blox 7 only every third SKY carries satellites), so taking just the
last SKY in a sample lost the satellite counts — HDOP appeared in the CoT but
sats_used/sats_seen never did.
"""

import json

from lincot.position import merge_sky

# Shapes observed live on aryaos-88d8 (gpsd 3.25, u-blox 7).
DOP_ONLY = json.dumps(
    {"class": "SKY", "device": "/dev/ttyACM0", "gdop": 8.9, "hdop": 4.2,
     "pdop": 7.9, "tdop": 4.1, "vdop": 6.7}
)
FULL_SKY = json.dumps(
    {"class": "SKY", "device": "/dev/ttyACM0", "hdop": 4.2, "nSat": 18, "uSat": 3,
     "satellites": [{"PRN": i, "used": i < 3} for i in range(18)]}
)


def test_full_sky_after_dop_only_is_not_lost():
    """The real-world ordering: the LAST SKY is DOP-only."""
    tpv = {"class": "TPV", "mode": 2, "lat": 37.76, "lon": -122.49}
    merge_sky(tpv, [DOP_ONLY, FULL_SKY, DOP_ONLY, DOP_ONLY])
    assert tpv["uSat"] == 3
    assert tpv["nSat"] == 18
    assert tpv["hdop"] == 4.2


def test_counts_derived_from_satellites_array():
    """Older gpsd omits uSat/nSat but still ships the satellites list."""
    sky = json.dumps(
        {"class": "SKY", "hdop": 1.2,
         "satellites": [{"PRN": 1, "used": True}, {"PRN": 2, "used": True},
                        {"PRN": 3, "used": False}]}
    )
    tpv = {"class": "TPV"}
    merge_sky(tpv, [sky])
    assert tpv["nSat"] == 3
    assert tpv["uSat"] == 2


def test_dop_only_still_yields_hdop():
    tpv = {"class": "TPV"}
    merge_sky(tpv, [DOP_ONLY])
    assert tpv["hdop"] == 4.2
    assert "uSat" not in tpv


def test_no_sky_and_garbage_are_safe():
    tpv = {"class": "TPV", "lat": 1.0}
    assert merge_sky(tpv, []) == {"class": "TPV", "lat": 1.0}
    assert merge_sky(tpv, ["not json", ""]) == {"class": "TPV", "lat": 1.0}
    assert merge_sky(tpv, None) == {"class": "TPV", "lat": 1.0}


def test_later_values_win():
    a = json.dumps({"class": "SKY", "hdop": 9.9})
    b = json.dumps({"class": "SKY", "hdop": 1.1})
    tpv = {"class": "TPV"}
    merge_sky(tpv, [a, b])
    assert tpv["hdop"] == 1.1
