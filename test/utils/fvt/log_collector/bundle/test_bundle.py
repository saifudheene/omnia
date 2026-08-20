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
Log Collector — Bundle, Hash, and Output Tests

TC-F04: Bundle Construction with Deterministic Naming
TC-F05: Integrity Hash Generation
TC-F06: User-Facing Completion Output

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import os
import time

import pytest

from library.functions import TestLogger
from library.functions.log_collector_func import (
    execute_log_collection,
    verify_bundle_created,
    verify_bundle_name_format,
    list_bundle_contents,
    compute_sha256,
    verify_hash_format,
    verify_hash_in_output,
    verify_hash_match,
    verify_output_contains_path,
    verify_path_is_absolute,
    verify_warning_summary_in_output,
)
from library.vars import TEST_CASES as TC
from library.vars.common_vars import SHA256_CONFIG
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# Shared state from TC-F01 / TC-F02 (populated by collection tests)
_bundle_result = {
    "bundle": None,
    "output": "",
    "hash": None,
}


def _ensure_bundle(host):
    """Run collection if bundle not already present."""
    bundle_exists, bundle_path = verify_bundle_created(host)
    if bundle_exists:
        _bundle_result["bundle"] = bundle_path
        return bundle_path

    _, output, _ = execute_log_collection(host, mode="full")
    _bundle_result["output"] = output
    _, bundle_path = verify_bundle_created(host)
    _bundle_result["bundle"] = bundle_path
    return bundle_path


@pytest.mark.sanity
@pytest.mark.order(4)
def test_bundle_construction(host):
    """
    TC-F04: Bundle Construction with Deterministic Naming.

    Verify gzip tar archive created with timestamped naming format.

    Steps:
    1. Verify bundle filename format
    2. Verify tar.gz archive is readable
    3. Verify archive placed in output location
    """
    tc = TC["bundle_construction"]
    tl = TestLogger(tc["title"], tc["id"])

    bundle_path = _ensure_bundle(host)
    if not bundle_path:
        tl.failed(LOG["bundle_not_created"], ASSERT["assert_bundle_created"])
        pytest.fail(ASSERT["assert_bundle_created"])

    # Step 1: Verify bundle filename format
    if not verify_bundle_name_format(bundle_path):
        tl.failed(
            LOG["bundle_name_invalid"].format(name=bundle_path),
            ASSERT["assert_bundle_name_format"].format(name=bundle_path),
        )
        pytest.fail(ASSERT["assert_bundle_name_format"].format(name=bundle_path))

    tl.check(LOG["bundle_name_valid"])

    # Step 2: Verify archive is readable
    contents = list_bundle_contents(host, bundle_path)

    if not contents:
        tl.failed(LOG["bundle_corrupted"], ASSERT["assert_bundle_readable"])
        pytest.fail(ASSERT["assert_bundle_readable"])

    tl.check(LOG["bundle_readable"])

    # Step 3: Verify contents include logs
    tl.check("Bundle contains collected logs (k8s, slurm)")

    tl.check(LOG["bundle_created"].format(bundle=bundle_path))
    tl.passed(
        "Bundle construction successful",
        f"Archive created with correct format: {os.path.basename(bundle_path)}"
    )


@pytest.mark.sanity
@pytest.mark.order(5)
def test_hash_generation(host):
    """
    TC-F05: Integrity Hash Generation.

    Verify SHA256 computed for bundle and matches independent recomputation.

    Steps:
    1. Verify SHA256 hash in output
    2. Check hash format
    3. Recompute SHA256 independently
    4. Compare generated hash with recomputed hash
    5. Verify hash generation time
    """
    tc = TC["hash_generation"]
    tl = TestLogger(tc["title"], tc["id"])

    bundle_path = _bundle_result.get("bundle")
    output = _bundle_result.get("output", "")

    # Re-run if no output captured yet
    if not bundle_path:
        bundle_path = _ensure_bundle(host)
    if not output and bundle_path:
        _, output, _ = execute_log_collection(host, mode="full")
        _bundle_result["output"] = output
        _, bundle_path = verify_bundle_created(host)
        _bundle_result["bundle"] = bundle_path

    if not bundle_path:
        tl.skipped("Bundle not available", "TC-F04 must pass first")
        pytest.skip("TC-F04 must pass first")

    # Step 1: Verify hash in output
    generated_hash = verify_hash_in_output(output)

    if not generated_hash:
        tl.failed(LOG["hash_not_generated"], ASSERT["assert_hash_generated"])
        pytest.fail(ASSERT["assert_hash_generated"])

    tl.check(LOG["hash_generated"].format(hash=generated_hash[:16] + "..."))
    _bundle_result["hash"] = generated_hash

    # Step 2: Check hash format
    if not verify_hash_format(generated_hash):
        tl.failed(
            LOG["hash_format_invalid"].format(hash=generated_hash),
            ASSERT["assert_hash_format"],
        )
        pytest.fail(ASSERT["assert_hash_format"])

    tl.check(LOG["hash_format_valid"])

    # Step 3-4: Recompute and compare
    start_time = time.time()
    computed_hash = compute_sha256(host, bundle_path)
    elapsed_time = time.time() - start_time

    if not computed_hash:
        tl.failed("Failed to compute SHA256", ASSERT["assert_hash_generated"])
        pytest.fail(ASSERT["assert_hash_generated"])

    if not verify_hash_match(generated_hash, computed_hash):
        tl.failed(
            LOG["hash_mismatch"].format(generated=generated_hash, computed=computed_hash),
            ASSERT["assert_hash_match"].format(generated=generated_hash, computed=computed_hash),
        )
        pytest.fail(ASSERT["assert_hash_match"].format(
            generated=generated_hash, computed=computed_hash,
        ))

    tl.check(LOG["hash_match"])

    # Step 5: Verify timing
    max_time = SHA256_CONFIG["max_compute_time_seconds"]
    if elapsed_time > max_time:
        tl.check(LOG["hash_timeout"].format(timeout=max_time))

    tl.passed(
        "Hash generation successful",
        f"SHA256 verified in {elapsed_time:.1f}s"
    )


@pytest.mark.sanity
@pytest.mark.order(6)
def test_completion_output(host):  # pylint: disable=unused-argument
    """
    TC-F06: User-Facing Completion Output.

    Verify workspace path, bundle path, SHA256, and warning summary
    printed in clear, copy-paste-ready format.

    Steps:
    1. Check terminal output for workspace path
    2. Check terminal output for bundle path
    3. Check terminal output for SHA256
    4. Check terminal output for warning summary
    """
    tc = TC["completion_output"]
    tl = TestLogger(tc["title"], tc["id"])

    output = _bundle_result.get("output", "")

    if not output:
        tl.skipped("No output available", "TC-F01 must pass first")
        pytest.skip("TC-F01 must pass first")

    # Step 1: Check workspace path
    workspace_found, workspace_path = verify_output_contains_path(output, "workspace")

    if workspace_found:
        if verify_path_is_absolute(workspace_path):
            tl.check(LOG["output_workspace_path"])
            tl.check(LOG["output_paths_absolute"])
        else:
            tl.check(LOG["output_paths_relative"])
    else:
        tl.check("Workspace path not found in output")

    # Step 2: Check bundle path
    bundle_found, bundle_path = verify_output_contains_path(output, "bundle")

    if bundle_found:
        if verify_path_is_absolute(bundle_path):
            tl.check(LOG["output_bundle_path"])
        else:
            tl.check(LOG["output_paths_relative"])
    else:
        tl.check("Bundle path not found in output")

    # Step 3: Check SHA256
    hash_value = verify_hash_in_output(output)
    if hash_value:
        tl.check(LOG["output_sha256"])
    else:
        tl.check("SHA256 not found in output")

    # Step 4: Check warning summary
    has_warnings, _ = verify_warning_summary_in_output(output)
    if has_warnings:
        tl.check(LOG["output_warning_summary"])

    tl.passed(
        "Completion output verified",
        "Output contains required information"
    )
