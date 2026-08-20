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
FVT — Metadata Synthesis and Inclusion

Verifies that ``metadata.json`` is generated inside the bundle run
folder with all required fields from ``metadata.json.j2`` template:
bundle_name, tar_relative_path, tar_sha256, timestamps (UTC+local),
trigger_user, oim_host_os, identifier, collection_mode,
exclusions_applied, warning_count, and warnings array.

Tests:
    TC-F03  Metadata Synthesis and Inclusion
"""

import pytest
from omnia_auto import TestLogger

from library.vars import TEST_CASES as TC
from library.vars.common_vars import METADATA_REQUIRED_FIELDS
from library.functions.log_collector_func import (
    get_workspace_directory,
    read_metadata,
    verify_metadata_exists,
    verify_metadata_valid_json,
    verify_metadata_required_fields,
    verify_metadata_collection_mode,
    verify_metadata_warning_entries,
)
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# ── TC-F03: Metadata Synthesis and Inclusion ────────────────────────────────

@pytest.mark.order(3)
@pytest.mark.functional
class TestMetadataSynthesis:
    """TC-F03 — Verify metadata.json synthesis and field completeness."""

    @pytest.fixture(autouse=True, scope="class")
    def _workspace(self, host, request):
        """Locate the most recent workspace for the class."""
        ws = get_workspace_directory(host)
        request.cls.workspace = ws

    def test_metadata_file_exists(self, host):
        """Verify metadata.json exists in the workspace run folder."""
        tc = TC["metadata_synthesis"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying metadata.json exists ...")
        assert self.workspace, ASSERT["metadata_missing"].format(
            detail="No workspace directory found"
        )

        exists = verify_metadata_exists(host, self.workspace)
        if exists:
            tl.passed(LOG["metadata_ok"], "metadata.json found")
        else:
            tl.failed(LOG["metadata_failed"], "metadata.json not found")
            assert False, ASSERT["metadata_missing"].format(
                detail=f"metadata.json not found in {self.workspace}"
            )

    def test_metadata_valid_json(self, host):
        """Verify metadata.json is valid JSON."""
        tc = TC["metadata_synthesis"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Validating JSON format ...")
        assert self.workspace, "No workspace"

        valid = verify_metadata_valid_json(host, self.workspace)
        if valid:
            tl.passed(LOG["metadata_ok"], "Valid JSON")
        else:
            tl.failed(LOG["metadata_failed"], "Invalid JSON")
            assert False, ASSERT["metadata_missing"].format(
                detail="metadata.json is not valid JSON"
            )

    def test_metadata_required_fields(self, host):
        """Verify all required fields from metadata.json.j2 are present."""
        tc = TC["metadata_synthesis"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking required metadata fields ...")
        assert self.workspace, "No workspace"

        metadata = read_metadata(host, self.workspace)
        assert metadata, ASSERT["metadata_missing"].format(
            detail="Could not read metadata.json"
        )

        all_present, missing = verify_metadata_required_fields(metadata)

        if all_present:
            tl.passed(LOG["metadata_ok"],
                      f"All {len(METADATA_REQUIRED_FIELDS)} fields present")
        else:
            tl.failed(LOG["metadata_failed"], f"Missing: {missing}")
            assert False, ASSERT["metadata_missing"].format(
                detail=f"Missing metadata fields: {missing}"
            )

    def test_metadata_collection_mode(self, host):
        """Verify collection_mode is 'complete logs' (default run)."""
        tc = TC["metadata_synthesis"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking collection_mode field ...")
        assert self.workspace, "No workspace"

        metadata = read_metadata(host, self.workspace)
        assert metadata, "Could not read metadata"

        mode_ok = verify_metadata_collection_mode(metadata, "complete logs")
        actual = metadata.get("collection_mode", "N/A")

        if mode_ok:
            tl.passed(LOG["metadata_ok"], f"mode={actual}")
        else:
            tl.failed(LOG["metadata_failed"],
                      f"Expected 'complete logs', got '{actual}'")
            assert False, ASSERT["metadata_missing"].format(
                detail=f"collection_mode mismatch: expected 'complete logs', "
                       f"got '{actual}'"
            )

    def test_metadata_sha256_populated(self, host):
        """Verify tar_sha256 field is populated (non-empty)."""
        tc = TC["metadata_synthesis"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking tar_sha256 field ...")
        assert self.workspace, "No workspace"

        metadata = read_metadata(host, self.workspace)
        assert metadata, "Could not read metadata"

        sha256 = metadata.get("tar_sha256", "")
        if sha256 and len(sha256) == 64:
            tl.passed(LOG["metadata_ok"], f"SHA256: {sha256[:16]}...")
        else:
            tl.failed(LOG["metadata_failed"],
                      f"tar_sha256 empty or invalid: '{sha256}'")
            assert False, ASSERT["metadata_missing"].format(
                detail=f"tar_sha256 not populated: '{sha256}'"
            )

    def test_metadata_warning_entries(self, host):
        """Verify warning entries have required fields (source, node_name, etc)."""
        tc = TC["metadata_synthesis"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Validating warning entry schema ...")
        assert self.workspace, "No workspace"

        metadata = read_metadata(host, self.workspace)
        assert metadata, "Could not read metadata"

        all_valid, missing = verify_metadata_warning_entries(metadata)
        warning_count = metadata.get("warning_count", 0)

        if all_valid:
            tl.passed(LOG["metadata_ok"],
                      f"warning_count={warning_count}, all entries valid")
        else:
            tl.failed(LOG["metadata_failed"],
                      f"Missing warning fields: {missing}")
            assert False, ASSERT["metadata_missing"].format(
                detail=f"Warning entries missing fields: {missing}"
            )
