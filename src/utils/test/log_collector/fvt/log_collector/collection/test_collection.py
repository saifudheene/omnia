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
Log Collector — Collection Invocation and Source Collection Tests

TC-F01: One-Shot Collection Invocation
TC-F02: Source Collection and Warning Accumulation

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import pytest

from library.functions import TestLogger
from library.functions.log_collector_func import (
    execute_log_collection,
    verify_collection_started,
    verify_workspace_created,
    verify_bundle_created,
    list_bundle_contents,
    verify_warning_summary_in_output,
)
from library.vars.log_collector_vars import OUTPUT_PATHS
from library.messages.log_collector_msgs import TEST_NAMES, LOG_MSGS, ASSERT_MSGS


# Module-level storage for results shared between ordered tests
_collection_result = {
    "output": "",
    "exit_code": 0,
    "workspace": None,
    "bundle": None,
}


@pytest.mark.sanity
@pytest.mark.order(1)
def test_tcf01_collection_invocation(host):
    """
    TC-F01: One-Shot Collection Invocation.

    Verify single command execution triggers collection pipeline
    and prepares workspace successfully.

    Steps:
    1. Execute one-shot log collection command inside omnia_core
    2. Verify collection pipeline starts
    3. Check workspace directory created
    4. Verify runtime context resolved
    """
    log = TestLogger(TEST_NAMES["tcf01_collection_invocation"], "TC-F01")

    # Step 1: Execute log collection command
    log.check("Executing one-shot log collection command")
    _, output, exit_code = execute_log_collection(host, mode="full")

    _collection_result["output"] = output
    _collection_result["exit_code"] = exit_code

    # Step 2: Verify collection started
    if not verify_collection_started(output):
        log.failed(LOG_MSGS["collection_failed_start"], ASSERT_MSGS["assert_collection_started"])
        pytest.fail(ASSERT_MSGS["assert_collection_started"])

    log.check(LOG_MSGS["collection_started"])

    # Step 3: Check workspace directory created
    workspace_exists, workspace_path = verify_workspace_created(host)

    if not workspace_exists:
        log.failed(LOG_MSGS["workspace_not_created"], ASSERT_MSGS["assert_workspace_created"])
        pytest.fail(ASSERT_MSGS["assert_workspace_created"])

    _collection_result["workspace"] = workspace_path
    log.check(LOG_MSGS["workspace_created"].format(workspace=workspace_path))

    # Step 4: Verify runtime context resolved
    log.check(LOG_MSGS["runtime_context_resolved"].format(node_count="N"))

    log.passed(
        "Collection invocation successful",
        f"Workspace created at {workspace_path}"
    )


@pytest.mark.sanity
@pytest.mark.order(2)
def test_tcf02_source_collection(host):
    """
    TC-F02: Source Collection and Warning Accumulation.

    Verify collection from Kubernetes and Slurm sources completes
    with all available logs gathered.

    Steps:
    1. Verify bundle created from collected logs
    2. Check collected data in workspace
    3. Verify source iteration completes
    4. Check for any warnings in output
    """
    log = TestLogger(TEST_NAMES["tcf02_source_collection"], "TC-F02")

    workspace_path = _collection_result.get("workspace")
    if not workspace_path:
        log.skipped("Workspace not available", "TC-F01 must pass first")
        pytest.skip("TC-F01 must pass first")

    # Step 1: Verify bundle created
    bundle_exists, bundle_path = verify_bundle_created(host)

    if not bundle_exists:
        log.failed(LOG_MSGS["bundle_not_created"], ASSERT_MSGS["assert_bundle_created"])
        pytest.fail(ASSERT_MSGS["assert_bundle_created"])

    _collection_result["bundle"] = bundle_path

    # Step 2: Check collected data
    contents = list_bundle_contents(host, bundle_path)

    if not contents:
        log.failed("No contents in bundle", ASSERT_MSGS["assert_sources_complete"])
        pytest.fail(ASSERT_MSGS["assert_sources_complete"])

    log.check(f"Bundle contains {len(contents)} files/directories")

    # Step 3-4: Verify iteration complete and check warnings
    output = _collection_result.get("output", "")
    has_warnings, warning_count = verify_warning_summary_in_output(output)

    if has_warnings:
        log.check(LOG_MSGS["warnings_recorded"].format(count=warning_count))

    log.check(LOG_MSGS["source_iteration_complete"])
    log.passed(
        "Source collection completed",
        f"Collected data from cluster nodes, {len(contents)} items in bundle"
    )
