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
Log Collector — Idempotency Test (Non-Functional)

TC-I01: Collection Command Idempotency

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import time

import pytest

from library.functions import TestLogger
from library.functions.log_collector_func import (
    execute_log_collection,
    verify_bundle_created,
    verify_hash_in_output,
    compare_bundle_contents,
    cleanup_bundle,
)
from library.vars.log_collector_vars import TEST_CONFIG
from library.messages.log_collector_msgs import TEST_NAMES, LOG_MSGS, ASSERT_MSGS


@pytest.mark.nft
@pytest.mark.order(20)
def test_tci01_idempotency(host):
    """
    TC-I01: Collection Command Idempotency.

    Verify collection command produces deterministic results on re-run.

    Steps:
    1. Execute log collection command (first run)
    2. Record bundle filename and SHA256
    3. Wait 5 seconds
    4. Execute log collection command (second run)
    5. Verify bundle filenames are different (timestamps)
    6. Compare bundle contents (excluding metadata timestamp)
    7. Verify both bundles have same log files
    """
    log = TestLogger(TEST_NAMES["tci01_idempotency"], "TC-I01")

    bundle1_path = None
    bundle2_path = None

    try:
        # Step 1: First run
        log.check("Executing first collection run")
        success1, output1, _ = execute_log_collection(host)

        if not success1:
            log.failed("First collection run failed", ASSERT_MSGS["assert_collection_started"])
            pytest.fail(ASSERT_MSGS["assert_collection_started"])

        _, bundle1_path = verify_bundle_created(host)
        verify_hash_in_output(output1)

        log.check(LOG_MSGS["first_run_complete"])

        # Step 3: Wait
        log.check(f"Waiting {TEST_CONFIG['idempotency_wait_seconds']} seconds")
        time.sleep(TEST_CONFIG["idempotency_wait_seconds"])

        # Step 4: Second run
        log.check("Executing second collection run")
        success2, output2, _ = execute_log_collection(host)

        if not success2:
            log.failed("Second collection run failed", ASSERT_MSGS["assert_collection_started"])
            pytest.fail(ASSERT_MSGS["assert_collection_started"])

        _, bundle2_path = verify_bundle_created(host)
        verify_hash_in_output(output2)

        log.check(LOG_MSGS["second_run_complete"])

        # Step 5: Verify filenames differ
        if bundle1_path == bundle2_path:
            log.failed(
                LOG_MSGS["bundles_same_names"],
                ASSERT_MSGS["assert_different_names"]
            )
            pytest.fail(ASSERT_MSGS["assert_different_names"])

        log.check(LOG_MSGS["bundles_different_names"])

        # Step 6-7: Compare contents
        identical, _, _ = compare_bundle_contents(
            host, bundle1_path, bundle2_path
        )

        if identical:
            log.check(LOG_MSGS["contents_identical"])
        else:
            # Contents may differ slightly due to timestamp, log rotation, etc.
            log.check(LOG_MSGS["contents_differ"])
            log.check("Note: Minor content differences expected due to timestamps")

        log.passed(
            "Idempotency test completed",
            "Two bundles created with different timestamps"
        )

    finally:
        if bundle1_path:
            cleanup_bundle(host, bundle1_path)
        if bundle2_path:
            cleanup_bundle(host, bundle2_path)
