#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Host identity helper tests."""

import lincot
from lincot import identity

VALID_ID = "0123456789abcdef0123456789abcdef"


def test_get_hostname_strips_domain(monkeypatch):
    """Dotted FQDNs are shortened to the host label."""
    monkeypatch.setattr("lincot.identity.socket.gethostname", lambda: "node.lan.ex")
    assert identity.get_hostname() == "node"


def test_get_hostname_plain(monkeypatch):
    """Short hostnames are returned as-is."""
    monkeypatch.setattr("lincot.identity.socket.gethostname", lambda: " aryaos ")
    assert identity.get_hostname() == "aryaos"


def test_get_hostname_empty(monkeypatch):
    """An empty hostname falls back to localhost."""
    monkeypatch.setattr("lincot.identity.socket.gethostname", lambda: "")
    assert identity.get_hostname() == "localhost"


def test_get_machine_id_second_path(monkeypatch, tmp_path):
    """Invalid and missing paths are skipped; uppercase is normalised."""
    bad = tmp_path / "bad"
    bad.write_text("not-a-machine-id\n", encoding="utf-8")
    good = tmp_path / "good"
    good.write_text(VALID_ID.upper() + "\n", encoding="utf-8")
    paths = (str(tmp_path / "missing"), str(bad), str(good))
    monkeypatch.setattr(lincot, "MACHINE_ID_PATHS", paths)
    assert identity.get_machine_id() == VALID_ID


def test_get_machine_id_none_valid(monkeypatch, tmp_path):
    """No valid machine-id yields None."""
    bad = tmp_path / "bad"
    bad.write_text("xyz", encoding="utf-8")
    paths = (str(bad), str(tmp_path / "missing"))
    monkeypatch.setattr(lincot, "MACHINE_ID_PATHS", paths)
    assert identity.get_machine_id() is None


def test_get_uid_uses_machine_id(monkeypatch):
    """Without an override the machine-id is the uid."""
    monkeypatch.setattr("lincot.identity.get_machine_id", lambda: VALID_ID)
    assert identity.get_uid({}) == VALID_ID
    assert identity.get_uid(None) == VALID_ID


def test_get_uid_falls_back_to_hostname(monkeypatch):
    """Without a machine-id the uid is derived from the hostname."""
    monkeypatch.setattr("lincot.identity.get_machine_id", lambda: None)
    monkeypatch.setattr("lincot.identity.get_hostname", lambda: "aryaos")
    assert identity.get_uid({}) == "lincot-aryaos"


def test_get_uid_override(monkeypatch):
    """COT_UID override is stripped and used."""
    monkeypatch.setattr("lincot.identity.get_machine_id", lambda: VALID_ID)
    assert identity.get_uid({"COT_UID": "  my-uid "}) == "my-uid"


def test_get_uid_whitespace_override_ignored(monkeypatch):
    """Whitespace-only COT_UID is ignored."""
    monkeypatch.setattr("lincot.identity.get_machine_id", lambda: VALID_ID)
    assert identity.get_uid({"COT_UID": "   "}) == VALID_ID


def test_get_callsign_override_and_default(monkeypatch):
    """CALLSIGN override is used; whitespace-only falls back to hostname."""
    monkeypatch.setattr("lincot.identity.get_hostname", lambda: "aryaos")
    assert identity.get_callsign({"CALLSIGN": " Alpha "}) == "Alpha"
    assert identity.get_callsign({"CALLSIGN": "  "}) == "aryaos"
    assert identity.get_callsign(None) == "aryaos"
