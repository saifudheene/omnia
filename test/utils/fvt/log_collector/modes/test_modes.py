# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
FVT — Collection Mode Compatibility

Verifies that both collection modes work correctly:

- **curated_support** mode: ``--tags curated_support`` triggers
  exclusion of temporary/stale files (*.tmp, *.temp, *.bak, *.gz,
  *.bz2, *.1-*.5) from the workspace before bundling.

- **full** mode (default / "complete logs"): All logs are included
  without exclusion filtering.

The ``collection_mode`` field in ``metadata.json`` reflects which
mode was active: ``"complete logs"`` or ``"curated_support"``.

Tests:
    TC-C01  Curated Support Mode — Exclude Temporary/Stale Logs
    TC-C02  Full Collection Mode — Include All Logs
"""

import pytest
from omnia_auto import TestLogger

from library.vars import TEST_CASES as TC
from library.vars.common_vars import COLLECTION_MODES
from library.functions.log_collector_func import (
    execute_log_collection,
    get_workspace_directory,
    read_metadata,
    verify_bundle_created,
    verify_collection_started,
    verify_metadata_collection_mode,
)
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# ── TC-C01: Curated Support Mode ───────────────────────────────────────────

@pytest.mark.order(7)
@pytest.mark.functional
class TestCuratedMode:
    """TC-C01 — Verify curated_support mode excludes temp/stale logs."""

    @pytest.fixture(autouse=True, scope="class")
    def _run_curated(self, host, request):
        """Execute collection in curated_support mode."""
        success, output, rc = execute_log_collection(
            host, mode="curated_support"
        )
        request.cls.output = output
        request.cls.success = success
        request.cls.rc = rc

    def test_curated_collection_succeeds(self, host):
        """Verify playbook completes in curated_support mode."""
        tc = TC["curated_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying curated_support collection ...")
        started = verify_collection_started(self.output)

        if self.success and started:
            tl.passed(LOG["mode_ok"],
                      "Curated support collection completed")
        else:
            tl.failed(LOG["mode_failed"],
                      f"Curated mode failed (rc={self.rc})")
            assert False, ASSERT["mode_mismatch"].format(
                expected="curated_support", actual=f"rc={self.rc}",
                detail="Playbook failed in curated_support mode"
            )

    def test_curated_metadata_mode(self, host):
        """Verify metadata.json shows collection_mode='curated_support'."""
        tc = TC["curated_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking collection_mode in metadata ...")
        workspace = get_workspace_directory(host)
        assert workspace, "No workspace directory"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata.json"

        mode_ok = verify_metadata_collection_mode(metadata, "curated_support")
        actual = metadata.get("collection_mode", "N/A")

        if mode_ok:
            tl.passed(LOG["mode_ok"], f"mode={actual}")
        else:
            tl.failed(LOG["mode_failed"],
                      f"Expected 'curated_support', got '{actual}'")
            assert False, ASSERT["mode_mismatch"].format(
                expected="curated_support", actual=actual,
                detail="metadata.json collection_mode does not match"
            )

    def test_curated_exclusions_applied(self, host):
        """Verify exclusions_applied is populated in curated mode."""
        tc = TC["curated_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking exclusions_applied field ...")
        workspace = get_workspace_directory(host)
        assert workspace, "No workspace"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata"

        exclusions = metadata.get("exclusions_applied", [])
        expected_patterns = COLLECTION_MODES["curated_support"]["exclusion_patterns"]

        if exclusions and len(exclusions) > 0:
            tl.passed(LOG["mode_ok"],
                      f"{len(exclusions)} exclusion patterns applied")
        else:
            tl.failed(LOG["mode_failed"],
                      "exclusions_applied is empty in curated mode")
            assert False, ASSERT["mode_mismatch"].format(
                expected=f"exclusions: {expected_patterns}",
                actual="exclusions_applied: []",
                detail="Curated mode should have non-empty exclusions_applied"
            )


# ── TC-C02: Full Collection Mode ───────────────────────────────────────────

@pytest.mark.order(8)
@pytest.mark.functional
class TestFullMode:
    """TC-C02 — Verify full/complete logs collection mode."""

    @pytest.fixture(autouse=True, scope="class")
    def _run_full(self, host, request):
        """Execute collection in full (default) mode."""
        success, output, rc = execute_log_collection(host, mode="full")
        request.cls.output = output
        request.cls.success = success
        request.cls.rc = rc

    def test_full_collection_succeeds(self, host):
        """Verify playbook completes in default full mode."""
        tc = TC["full_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying full collection ...")
        started = verify_collection_started(self.output)

        if self.success and started:
            tl.passed(LOG["mode_ok"], "Full collection completed")
        else:
            tl.failed(LOG["mode_failed"],
                      f"Full mode failed (rc={self.rc})")
            assert False, ASSERT["mode_mismatch"].format(
                expected="complete logs", actual=f"rc={self.rc}",
                detail="Playbook failed in full mode"
            )

    def test_full_metadata_mode(self, host):
        """Verify metadata.json shows collection_mode='complete logs'."""
        tc = TC["full_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking collection_mode in metadata ...")
        workspace = get_workspace_directory(host)
        assert workspace, "No workspace"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata"

        mode_ok = verify_metadata_collection_mode(metadata, "complete logs")
        actual = metadata.get("collection_mode", "N/A")

        if mode_ok:
            tl.passed(LOG["mode_ok"], f"mode={actual}")
        else:
            tl.failed(LOG["mode_failed"],
                      f"Expected 'complete logs', got '{actual}'")
            assert False, ASSERT["mode_mismatch"].format(
                expected="complete logs", actual=actual,
                detail="metadata.json collection_mode does not match"
            )

    def test_full_no_exclusions(self, host):
        """Verify exclusions_applied is empty in full mode."""
        tc = TC["full_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking exclusions_applied is empty ...")
        workspace = get_workspace_directory(host)
        assert workspace, "No workspace"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata"

        exclusions = metadata.get("exclusions_applied", [])

        if not exclusions:
            tl.passed(LOG["mode_ok"], "No exclusions in full mode")
        else:
            tl.failed(LOG["mode_failed"],
                      f"Unexpected exclusions: {exclusions}")
            assert False, ASSERT["mode_mismatch"].format(
                expected="exclusions_applied: []",
                actual=f"exclusions_applied: {exclusions}",
                detail="Full mode should have empty exclusions_applied"
            )

    def test_full_bundle_created(self, host):
        """Verify bundle was created in full mode."""
        tc = TC["full_mode"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying bundle exists ...")
        exists, path = verify_bundle_created(host)

        if exists:
            tl.passed(LOG["mode_ok"], f"Bundle: {path}")
        else:
            tl.failed(LOG["mode_failed"], "No bundle after full collection")
            assert False, ASSERT["mode_mismatch"].format(
                expected="bundle created", actual="no bundle",
                detail="Bundle not created after full mode collection"
            )
