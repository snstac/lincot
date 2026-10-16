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

"""Guard rails for the release half of .github/workflows/ci.yml.

Every tag build from v1.2.0 to v1.3.9 went red in "Publish to PyPI" while the
same commit was green on main: PyPI trusted publishing rejected the OIDC token
(``invalid-publisher``) because no publisher was registered for this
workflow/environment pair. Nothing on a branch or PR exercised that path, so
the first sign of trouble was always a broken release.

These tests pin the parts of the workflow that the PyPI-side registration and
the dry run depend on, so they cannot drift silently:

* the publisher identity PyPI must match (workflow file + environment name);
* a ``workflow_dispatch`` dry run that builds every artifact;
* no job that can run on a dispatch is able to publish anything.
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

# What PyPI's trusted publisher for the `lincot` project must be registered
# with. docs/releasing.md documents the same values for maintainers.
PYPI_WORKFLOW_FILE = "ci.yml"
PYPI_ENVIRONMENT = "pypi"

PUBLISH_ACTIONS = ("pypa/gh-action-pypi-publish", "softprops/action-gh-release")
TAG_PUSH_ONLY = "github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')"
TAG_OR_DISPATCH = (
    "startsWith(github.ref, 'refs/tags/') || github.event_name == 'workflow_dispatch'"
)


@pytest.fixture(scope="module")
def workflow():
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) reads the bare key `on` as boolean True.
    doc["on"] = doc.pop(True, doc.get("on"))
    return doc


def _uses(job):
    return [step.get("uses", "") for step in job.get("steps", [])]


def _publishes(job):
    perms = job.get("permissions") or {}
    return (
        any(u.startswith(PUBLISH_ACTIONS) for u in _uses(job))
        or perms.get("id-token") == "write"
        or perms.get("contents") == "write"
        or "environment" in job
    )


def _env_name(job):
    env = job.get("environment")
    return env.get("name") if isinstance(env, dict) else env


def test_workflow_file_name_matches_pypi_publisher():
    """Renaming ci.yml silently breaks trusted publishing on the next tag."""
    assert WORKFLOW.name == PYPI_WORKFLOW_FILE
    docs = (ROOT / "docs" / "releasing.md").read_text(encoding="utf-8")
    assert f"`{PYPI_WORKFLOW_FILE}`" in docs
    assert f"`{PYPI_ENVIRONMENT}`" in docs


def test_pypi_job_uses_registered_environment_and_oidc(workflow):
    job = workflow["jobs"]["package-pypi"]
    assert _env_name(job) == PYPI_ENVIRONMENT
    assert job["permissions"] == {"id-token": "write"}


def test_default_token_is_read_only(workflow):
    """Write scopes are granted per job, only to the jobs that publish."""
    assert workflow["permissions"] == {"contents": "read"}


def test_workflow_dispatch_dry_run_exists(workflow):
    assert "workflow_dispatch" in workflow["on"]


@pytest.mark.parametrize("name", ["build-dist", "package-deb", "package-rpm"])
def test_dry_run_builds_every_release_artifact(workflow, name):
    job = workflow["jobs"][name]
    assert job.get("if") in (None, TAG_OR_DISPATCH), job.get("if")
    assert not _publishes(job)


def test_every_publishing_job_is_tag_push_only(workflow):
    """A dispatch -- even one started from a tag ref -- must never publish.

    ``startsWith(github.ref, 'refs/tags/')`` alone is not enough: a manual run
    launched against a tag has a tag ref too.
    """
    publishers = {n: j for n, j in workflow["jobs"].items() if _publishes(j)}
    assert {"package-pypi", "release"} <= set(publishers)
    for name, job in publishers.items():
        # Exact match: a substring check would accept `... || ...`.
        assert job.get("if") == TAG_PUSH_ONLY, name


def test_release_waits_for_version_check(workflow):
    """A tag that does not match VERSION must not produce a GitHub Release."""
    assert "build-dist" in workflow["jobs"]["release"]["needs"]


def test_pypi_uploads_the_checked_build(workflow):
    """Publish exactly what build-dist verified, rather than rebuilding it."""
    job = workflow["jobs"]["package-pypi"]
    assert "build-dist" in job["needs"]
    assert not any(u.startswith("actions/checkout") for u in _uses(job))
    build = workflow["jobs"]["build-dist"]
    runs = " ".join(step.get("run", "") for step in build["steps"])
    assert "twine check --strict" in runs
    assert "VERSION" in runs
