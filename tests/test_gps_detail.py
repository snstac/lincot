"""Tests for nerdy GPS detail in the LINCOT position CoT."""

import xml.etree.ElementTree as ET

from lincot.functions import position_to_cot_xml


def _tpv():
    return {
        "class": "TPV",
        "mode": 3,
        "lat": 37.76,
        "lon": -122.49,
        "altHAE": 12.0,
        "speed": 0.4,
        "track": 90.0,
        "eph": 5.0,
        "epv": 8.0,
        "hdop": 0.9,
        "nSat": 11,
        "uSat": 8,
    }


def test_position_cot_has_gps_detail():
    event = position_to_cot_xml(_tpv(), {})
    assert event is not None

    pl = event.find(".//precisionlocation")
    assert pl is not None and pl.get("geopointsrc") == "GPS"

    gps = event.find(".//__gps")
    assert gps is not None
    assert gps.get("fix") == "3D"
    assert gps.get("sats_used") == "8"
    assert gps.get("sats_seen") == "11"
    assert gps.get("hdop") == "0.9"

    remarks = event.find(".//remarks")
    assert remarks is not None and "3D fix" in remarks.text
    assert "8/11 sats" in remarks.text


def test_no_fix_marks_none():
    tpv = _tpv()
    tpv["mode"] = 1
    event = position_to_cot_xml(tpv, {})
    gps = event.find(".//__gps")
    assert gps is not None and gps.get("fix") == "none"
