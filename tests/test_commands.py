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

"""Command line entry point tests."""

import runpy
import sys

import pytak

from lincot import commands


def test_main_calls_pytak_cli(monkeypatch):
    """main() hands off to pytak.cli with the package name."""
    calls = []
    monkeypatch.setattr(pytak, "cli", calls.append)
    commands.main()
    assert calls == ["lincot"]


def test_module_runs_as_script(monkeypatch):
    """`python -m lincot.commands` must still load the `lincot` app.

    Regression: main() derived the app name from __name__, which is
    "__main__" here, so pytak.cli imported __main__ and read the wrong
    config section.
    """
    calls = []
    monkeypatch.setattr(pytak, "cli", calls.append)
    monkeypatch.delitem(sys.modules, "lincot.commands", raising=False)
    runpy.run_module("lincot.commands", run_name="__main__")
    assert calls == ["lincot"]
