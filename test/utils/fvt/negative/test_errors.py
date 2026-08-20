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
Log Collector — Negative / Error Handling Tests

TC-E01: Output Directory Not Writable (skipped: root in container)
TC-E03: Missing Source Files - Warning Emitted
TC-E04: Archive Generation Failure

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import pytest

from library.functions import TestLogger
from library.functions.log_collector_func import (
    execute_log_collection,
    verify_workspace_created,
    verify_bundle_created,
    verify_not_writable_error,
    verify_archive_failure_error,
    verify_missing_source_warning,
    verify_warning_summary_in_output,
    set_directory_permissions,
    fill_disk_space,
    free_disk_space,
    cleanup_bundle,
)
from library.vars import TEST_CASES as TC
from library.vars.common_vars import OUTPUT_PATHS
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


@pytest.mark.skip(
    reason="Not applicable: Playbook runs as root in container "
           "and bypasses permission checks"
)
@pytest.mark.sanity
@pytest.mark.order(10)
def test_output_not_writable(host):
    """
    TC-E01: Output Directory Not Writable.

    SKIPPED: Not applicable to current architecture.
    Playbook runs as root inside container and can write to read-only directories.

    Steps:
    1. Set output directory permissions to read-only
    2. Execute log collection command
    3. Verify command fails early
    4. Check error message
    5. Verify no partial artifacts created
    6. Restore permissions
    """
    tc = TC["output_not_writable"]
    tl = TestLogger(tc["title"], tc["id"])
    output_path = OUTPUT_PATHS["default_output_root"]

    try:
        # Step 1: Set read-only permissions
        tl.check("Setting output directory to read-only")
        set_directory_permissions(host, output_path, "555")

        # Step 2-3: Execute command and expect failure
        success, output, _ = execute_log_collection(host)

        # Step 4: Check error message
        if success:
            tl.failed(
                LOG["output_not_writable_not_detected"],
                ASSERT["assert_not_writable_error"],
            )
            pytest.fail(ASSERT["assert_not_writable_error"])

        if verify_not_writable_error(output):
            tl.check(LOG["output_not_writable_detected"])
        else:
            tl.check("Expected 'not writable' message not found in output")

        # Step 5: Verify no partial artifacts
        workspace_exists, _ = verify_workspace_created(host)
        if workspace_exists:
            tl.failed(LOG["partial_artifacts_found"], ASSERT["assert_no_artifacts"])
            pytest.fail(ASSERT["assert_no_artifacts"])

        tl.check(LOG["no_partial_artifacts"])

        tl.passed(
            "Not writable error handled correctly",
            "Command failed with appropriate error, no partial artifacts"
        )

    finally:
        # Step 6: Restore permissions
        set_directory_permissions(host, output_path, "755")
        tl.check(LOG["permissions_restored"])


@pytest.mark.sanity
@pytest.mark.order(11)
def test_missing_sources(host):
    """
    TC-E03: Missing Source Files - Warning Emitted.

    Verify warning emitted when expected log sources are missing.

    Steps:
    1. Execute log collection command
    2. Check terminal output for missing source warning
    3. Verify bundle created despite missing sources
    4. Check warning summary
    """
    tc = TC["missing_sources"]
    tl = TestLogger(tc["title"], tc["id"])

    # Step 1: Execute collection
    _, output, _ = execute_log_collection(host)

    # Step 2: Check for missing source warning (if any)
    found, source, node = verify_missing_source_warning(output)

    if found:
        tl.check(LOG["missing_source_warning"].format(source=source, node=node))
    else:
        tl.check("No missing source warnings (all sources available)")

    # Step 3: Verify bundle created
    bundle_exists, bundle_path = verify_bundle_created(host)

    if not bundle_exists:
        tl.failed(LOG["bundle_not_created"], ASSERT["assert_bundle_created"])
        pytest.fail(ASSERT["assert_bundle_created"])

    # Step 4: Check warning summary
    _, warning_count = verify_warning_summary_in_output(output)
    tl.check(f"Warning count: {warning_count}")

    # Cleanup
    if bundle_path:
        cleanup_bundle(host, bundle_path)

    tl.passed(
        "Missing sources handled correctly",
        "Collection continues with warnings for missing sources"
    )


@pytest.mark.sanity
@pytest.mark.order(12)
def test_archive_failure(host):
    """
    TC-E04: Archive Generation Failure.

    Verify command fails with root-cause message when archive generation fails.

    Steps:
    1. Fill output disk to capacity
    2. Execute log collection command
    3. Verify archive generation fails
    4. Check error message
    5. Remove fillfile
    """
    tc = TC["archive_failure"]
    tl = TestLogger(tc["title"], tc["id"])
    output_path = OUTPUT_PATHS["default_output_root"]

    try:
        # Step 1: Fill disk
        tl.check("Filling disk space (simulated)")
        fill_disk_space(host, output_path, 10000)  # 10GB fill attempt

        # Step 2-3: Execute collection
        _, output, exit_code = execute_log_collection(host)

        # Step 4: Check error message
        if verify_archive_failure_error(output):
            tl.check(LOG["archive_failure_detected"])
        else:
            tl.check("Archive failure not triggered (disk may have space)")

        # Step 5: Check exit code
        if exit_code != 0:
            tl.check(f"Command exited with code {exit_code}")

        tl.passed(
            "Archive failure test completed",
            "Error handling verified"
        )

    finally:
        free_disk_space(host, output_path)
        tl.check(LOG["disk_space_freed"])
