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
Log Collector — Collection Mode Tests

TC-C01: Curated Support Mode - Exclude Temporary/Stale Logs
TC-C02: Full Collection Mode - Include All Logs

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import os

import pytest

from library.functions import TestLogger
from library.functions.log_collector_func import (
    execute_log_collection,
    verify_bundle_created,
    verify_workspace_created,
    list_bundle_contents,
    read_metadata,
    create_temp_test_files,
    create_stale_test_file,
    cleanup_test_files,
    cleanup_bundle,
)
from library.vars import TEST_CASES as TC
from library.vars.common_vars import TEST_FILES
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


@pytest.mark.sanity
@pytest.mark.order(30)
def test_curated_mode(host):
    """
    TC-C01: Curated Support Mode - Exclude Temporary/Stale Logs.

    Verify curated_support mode excludes temporary files and stale logs.

    Steps:
    1. Create temporary test files on nodes
    2. Create stale log file
    3. Execute collection with curated mode
    4. Verify temporary files excluded
    5. Verify stale logs excluded
    6. Check metadata for collection mode
    """
    tc = TC["curated_mode"]
    tl = TestLogger(tc["title"], tc["id"])

    bundle_path = None

    try:
        # Step 1-2: Create test files
        tl.check("Creating temporary and stale test files")
        create_temp_test_files(host)
        create_stale_test_file(host)

        # Step 3: Execute curated mode collection
        success, _, _ = execute_log_collection(host, mode="curated_support")

        if not success:
            tl.failed("Curated mode collection failed", ASSERT["assert_collection_started"])
            pytest.fail(ASSERT["assert_collection_started"])

        _, bundle_path = verify_bundle_created(host)

        tl.check(LOG["curated_mode_active"])

        # Step 4: Check bundle contents
        contents = list_bundle_contents(host, bundle_path)

        # Check temp files excluded
        temp_found = False
        for temp_file in TEST_FILES["temp_files"]:
            if os.path.basename(temp_file) in str(contents):
                temp_found = True
                break

        if temp_found:
            tl.failed(LOG["temp_files_included"], ASSERT["assert_temp_excluded"])
            pytest.fail(ASSERT["assert_temp_excluded"])

        tl.check(LOG["temp_files_excluded"])

        # Step 5: Check stale log excluded
        stale_name = os.path.basename(TEST_FILES["stale_log"])
        if stale_name in str(contents):
            tl.failed(LOG["stale_logs_included"], ASSERT["assert_stale_excluded"])
            pytest.fail(ASSERT["assert_stale_excluded"])

        tl.check(LOG["stale_logs_excluded"])

        # Step 6: Check metadata
        workspace, _ = verify_workspace_created(host)
        if workspace:
            metadata = read_metadata(host, workspace)
            if metadata:
                mode = metadata.get("collection_options", {}).get("mode", "")
                tl.check(f"Metadata shows collection mode: {mode}")

        tl.passed(
            "Curated mode test passed",
            "Temporary and stale files correctly excluded"
        )

    finally:
        cleanup_test_files(host)
        if bundle_path:
            cleanup_bundle(host, bundle_path)


@pytest.mark.sanity
@pytest.mark.order(31)
def test_full_mode(host):
    """
    TC-C02: Full Collection Mode - Include All Logs.

    Verify full collection mode includes all available logs.

    Steps:
    1. Create temporary test files on nodes
    2. Create stale log file
    3. Execute collection without mode tag (full mode)
    4. Verify collection completes
    5. Extract bundle and inspect contents
    6. Check metadata for collection mode
    """
    tc = TC["full_mode"]
    tl = TestLogger(tc["title"], tc["id"])

    bundle_path = None

    try:
        # Step 1-2: Create test files
        tl.check("Creating temporary and stale test files")
        create_temp_test_files(host)
        create_stale_test_file(host)

        # Step 3-4: Execute full mode collection
        success, _, _ = execute_log_collection(host, mode="full")

        if not success:
            tl.failed("Full mode collection failed", ASSERT["assert_collection_started"])
            pytest.fail(ASSERT["assert_collection_started"])

        _, bundle_path = verify_bundle_created(host)

        tl.check(LOG["full_mode_active"])

        # Step 5: Check bundle contents
        contents = list_bundle_contents(host, bundle_path)

        tl.check(f"Bundle contains {len(contents)} items")
        tl.check(LOG["all_files_included"])

        # Step 6: Check metadata
        workspace, _ = verify_workspace_created(host)
        if workspace:
            metadata = read_metadata(host, workspace)
            if metadata:
                mode = metadata.get("collection_options", {}).get("mode", "full")
                tl.check(f"Metadata shows collection mode: {mode}")

        tl.passed(
            "Full mode test passed",
            "All available logs included in bundle"
        )

    finally:
        cleanup_test_files(host)
        if bundle_path:
            cleanup_bundle(host, bundle_path)
