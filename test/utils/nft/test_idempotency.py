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
NFT — Collection Command Idempotency

Verifies that running ``ansible-playbook collect.yml`` twice in
succession produces bundles with identical log content (excluding
timestamp-dependent metadata).

Each run creates a new ``omnia_logs_<timestamp>/`` directory, so we
compare the content checksums (excluding metadata.json) of the two
bundles.

Tests:
    TC-I01  Collection Command Idempotency
"""

import time

import pytest
from omnia_auto import TestLogger

from library.vars import TEST_CASES as TC
from library.vars.common_vars import TEST_CONFIG
from library.functions.log_collector_func import (
    compare_bundle_contents,
    execute_log_collection,
    get_bundle_path,
    verify_bundle_created,
    verify_collection_started,
)
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# ── TC-I01: Collection Command Idempotency ─────────────────────────────────

@pytest.mark.order(12)
@pytest.mark.nft
class TestIdempotency:
    """TC-I01 — Verify idempotent collection produces identical content."""

    def test_idempotency(self, host):
        """
        Run collection twice and compare bundle contents.

        Steps:
        1. Execute first collection run
        2. Record first bundle path
        3. Wait briefly for timestamp separation
        4. Execute second collection run
        5. Record second bundle path
        6. Compare content checksums (excluding metadata.json)
        """
        tc = TC["idempotency"]
        tl = TestLogger(tc["title"], tc["id"])

        # ── Run 1 ──────────────────────────────────────────────────────
        tl.check("Executing first collection run ...")
        success1, output1, rc1 = execute_log_collection(host)

        assert success1, ASSERT["idempotency_failed"].format(
            checksum1="N/A", checksum2="N/A",
            detail=f"First run failed (rc={rc1})"
        )
        assert verify_collection_started(output1), \
            "First run did not start properly"

        bundle1 = get_bundle_path(host)
        assert bundle1, "First bundle not found"
        tl.check(f"  Run 1 bundle: {bundle1}")

        # ── Wait ───────────────────────────────────────────────────────
        wait = TEST_CONFIG["idempotency_wait_seconds"]
        tl.check(f"Waiting {wait}s between runs ...")
        time.sleep(wait)

        # ── Run 2 ──────────────────────────────────────────────────────
        tl.check("Executing second collection run ...")
        success2, output2, rc2 = execute_log_collection(host)

        assert success2, ASSERT["idempotency_failed"].format(
            checksum1="N/A", checksum2="N/A",
            detail=f"Second run failed (rc={rc2})"
        )

        bundle2 = get_bundle_path(host)
        assert bundle2, "Second bundle not found"
        tl.check(f"  Run 2 bundle: {bundle2}")

        # Bundles should be different files (different timestamps)
        assert bundle1 != bundle2, \
            "Both runs produced the same bundle path — timestamp not unique"

        # ── Compare ────────────────────────────────────────────────────
        tl.check("Comparing bundle contents ...")
        identical, cs1, cs2 = compare_bundle_contents(
            host, bundle1, bundle2
        )

        if identical:
            tl.passed(
                LOG["idempotency_ok"],
                f"Content checksums match: {cs1[:16]}..."
            )
        else:
            tl.failed(
                LOG["idempotency_failed"],
                f"Checksums differ: {cs1[:16]}... vs {cs2[:16]}..."
            )
            assert False, ASSERT["idempotency_failed"].format(
                checksum1=cs1, checksum2=cs2,
                detail="Bundle contents differ between consecutive runs"
            )
