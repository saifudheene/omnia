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
FVT — Negative / Error Handling

Verifies that the log collector handles error conditions gracefully:

- **Output directory not writable**: bundle.yml validates the output
  root is writable before archiving.

- **Missing source files**: The k8s_logs.yml and slurm_logs.yml tasks
  stat each expected log path and record ``missing_source`` warnings
  for any that don't exist.

- **SSH collection failure**: The rescue blocks in main.yml catch SSH
  failures and record ``unreachable`` / ``collection_error`` warnings.
  bundle.yml creates ``SSH_COLLECTION_FAILED.txt`` placeholder files
  for failed nodes.

Tests:
    TC-E01  Output Directory Not Writable
    TC-E03  Missing Source Files — Warning Emitted
    TC-E04  Archive Generation Failure
"""

import pytest
from omnia_auto import TestLogger

from library.vars import TEST_CASES as TC
from library.vars.common_vars import OUTPUT_PATHS
from library.functions.log_collector_func import (
    execute_log_collection,
    find_ssh_failure_markers,
    get_workspace_directory,
    read_metadata,
    set_directory_permissions,
    verify_metadata_warning_entries,
    verify_warning_message_format,
)
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# ── TC-E01: Output Directory Not Writable ──────────────────────────────────

@pytest.mark.order(9)
@pytest.mark.functional
class TestOutputNotWritable:
    """TC-E01 — Verify graceful handling when output root is not writable."""

    def test_not_writable_detected(self, host):
        """
        Make the output root read-only, run collection, verify failure
        is detected and reported, then restore permissions.
        """
        tc = TC["output_not_writable"]
        tl = TestLogger(tc["title"], tc["id"])

        output_root = OUTPUT_PATHS["default_output_root"]

        # Ensure the directory exists first
        from omnia_auto import run_on_host
        run_on_host(host, f"mkdir -p {output_root}")

        tl.check("Making output root read-only ...")
        set_directory_permissions(host, output_root, "555")

        try:
            tl.check("Running collection with read-only output ...")
            success, output, rc = execute_log_collection(host)

            # The playbook should fail because bundle.yml validates
            # write permission with a test file
            if not success or rc != 0:
                tl.passed(
                    LOG["error_handled"],
                    f"Correctly failed with rc={rc}"
                )
            else:
                tl.failed(
                    LOG["error_not_handled"],
                    "Collection succeeded despite read-only output"
                )
                assert False, ASSERT["error_not_detected"].format(
                    error_type="output_not_writable",
                    detail="Playbook should fail when output root is 555"
                )
        finally:
            tl.check("Restoring output root permissions ...")
            set_directory_permissions(host, output_root, "755")


# ── TC-E03: Missing Source Files — Warning Emitted ─────────────────────────

@pytest.mark.order(10)
@pytest.mark.functional
class TestMissingSources:
    """TC-E03 — Verify missing log sources produce warnings, not failures."""

    def test_missing_sources_produce_warnings(self, host):
        """
        Run collection normally; verify that any missing log paths
        on target nodes are recorded as missing_source warnings in
        metadata.json rather than causing playbook failure.
        """
        tc = TC["missing_sources"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Running collection to check for source warnings ...")
        success, output, rc = execute_log_collection(host)

        # Collection should succeed even if some sources are missing
        assert success, ASSERT["error_not_detected"].format(
            error_type="missing_sources",
            detail=f"Collection failed entirely (rc={rc})"
        )

        tl.check("Reading metadata for warning entries ...")
        workspace = get_workspace_directory(host)
        assert workspace, "No workspace found"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata"

        warnings = metadata.get("warnings", [])
        missing_warnings = [
            w for w in warnings
            if w.get("reason") == "missing_source"
        ]

        tl.check(f"Found {len(missing_warnings)} missing_source warnings")

        # Validate warning entry schema
        all_valid, missing_fields = verify_metadata_warning_entries(metadata)

        if all_valid:
            tl.passed(
                LOG["error_handled"],
                f"{len(missing_warnings)} missing-source warnings recorded, "
                f"all with valid schema"
            )
        else:
            tl.failed(
                LOG["error_not_handled"],
                f"Warning entries missing fields: {missing_fields}"
            )
            assert False, ASSERT["error_not_detected"].format(
                error_type="missing_sources",
                detail=f"Warning schema incomplete: {missing_fields}"
            )

    def test_missing_source_message_format(self, host):
        """Verify missing_source warning messages contain path and node info."""
        tc = TC["missing_sources"]
        tl = TestLogger(tc["title"], tc["id"])

        workspace = get_workspace_directory(host)
        if not workspace:
            pytest.skip("No workspace — cannot verify warning format")

        metadata = read_metadata(host, workspace)
        if not metadata:
            pytest.skip("Cannot read metadata")

        warnings = metadata.get("warnings", [])
        missing_warnings = [
            w for w in warnings if w.get("reason") == "missing_source"
        ]

        if not missing_warnings:
            tl.passed(LOG["error_handled"],
                      "No missing-source warnings to validate")
            return

        tl.check(f"Validating {len(missing_warnings)} warning messages ...")
        all_valid = all(
            "missing" in w.get("message", "").lower()
            and w.get("node_name", "")
            for w in missing_warnings
        )

        if all_valid:
            tl.passed(LOG["error_handled"],
                      "All missing-source messages valid")
        else:
            tl.failed(LOG["error_not_handled"],
                      "Some warnings have invalid message format")
            assert False, ASSERT["error_not_detected"].format(
                error_type="missing_sources",
                detail="Warning message missing path or node info"
            )


# ── TC-E04: Archive Generation Failure ─────────────────────────────────────

@pytest.mark.order(11)
@pytest.mark.functional
class TestArchiveFailure:
    """TC-E04 — Verify SSH collection failures create placeholder markers."""

    def test_ssh_failure_markers(self, host):
        """
        After a normal collection run, check for SSH_COLLECTION_FAILED.txt
        placeholder files. These are created by bundle.yml for any nodes
        that were unreachable or had collection errors.
        """
        tc = TC["archive_failure"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Searching for SSH failure marker files ...")
        markers = find_ssh_failure_markers(host)

        if markers:
            tl.check(f"Found {len(markers)} failure markers")
            # Read first marker to verify content format
            from omnia_auto import run_on_host
            from library.vars.common_vars import CMDS
            content = run_on_host(
                host,
                CMDS["read_failure_marker"].format(marker_path=markers[0])
            ).stdout

            has_fields = all(
                field in content
                for field in ["Node Name", "Reason", "Message"]
            )

            if has_fields:
                tl.passed(
                    LOG["error_handled"],
                    f"{len(markers)} markers with valid format"
                )
            else:
                tl.failed(LOG["error_not_handled"],
                          "Marker file missing expected fields")
                assert False, ASSERT["error_not_detected"].format(
                    error_type="archive_failure",
                    detail="SSH_COLLECTION_FAILED.txt missing fields"
                )
        else:
            # No failures is acceptable — all nodes were reachable
            tl.passed(LOG["error_handled"],
                      "No SSH failure markers (all nodes reachable)")

    def test_unreachable_warnings_in_metadata(self, host):
        """Verify unreachable node warnings appear in metadata."""
        tc = TC["archive_failure"]
        tl = TestLogger(tc["title"], tc["id"])

        workspace = get_workspace_directory(host)
        if not workspace:
            pytest.skip("No workspace")

        metadata = read_metadata(host, workspace)
        if not metadata:
            pytest.skip("Cannot read metadata")

        warnings = metadata.get("warnings", [])
        unreachable = [
            w for w in warnings
            if w.get("reason") in ("unreachable", "collection_error")
        ]

        tl.check(f"Found {len(unreachable)} unreachable/error warnings")

        if unreachable:
            # Validate each warning has proper format
            all_valid = all(
                verify_warning_message_format(w) for w in unreachable
            )
            if all_valid:
                tl.passed(LOG["error_handled"],
                          f"{len(unreachable)} warnings with valid format")
            else:
                tl.failed(LOG["error_not_handled"],
                          "Some unreachable warnings have bad format")
                assert False, ASSERT["error_not_detected"].format(
                    error_type="archive_failure",
                    detail="Unreachable warning message format invalid"
                )
        else:
            tl.passed(LOG["error_handled"],
                      "No unreachable warnings (all nodes responded)")
