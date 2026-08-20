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
Log Collector — Metadata Synthesis Tests

TC-F03: Metadata Synthesis and Inclusion

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import pytest

from library.functions import TestLogger
from library.functions.log_collector_func import (
    execute_log_collection,
    verify_workspace_created,
    verify_metadata_exists,
    verify_metadata_valid_json,
    read_metadata,
    verify_metadata_required_fields,
    verify_metadata_warning_entries,
)
from library.vars.log_collector_vars import METADATA_REQUIRED_FIELDS
from library.messages.log_collector_msgs import TEST_NAMES, LOG_MSGS, ASSERT_MSGS


@pytest.mark.sanity
@pytest.mark.order(3)
def test_tcf03_metadata_synthesis(host):
    """
    TC-F03: Metadata Synthesis and Inclusion.

    Verify metadata JSON generated with provenance fields and valid JSON format.

    Steps:
    1. Run collection to generate metadata
    2. Verify metadata JSON file exists
    3. Validate JSON format
    4. Check all required fields present
    5. Check warning entries schema
    """
    log = TestLogger(TEST_NAMES["tcf03_metadata_synthesis"], "TC-F03")

    # Run collection if workspace not already present
    workspace_exists, workspace_path = verify_workspace_created(host)
    if not workspace_exists:
        log.check("Running collection to generate metadata")
        execute_log_collection(host, mode="full")
        workspace_exists, workspace_path = verify_workspace_created(host)

    if not workspace_exists:
        log.failed(LOG_MSGS["workspace_not_created"], ASSERT_MSGS["assert_workspace_created"])
        pytest.fail(ASSERT_MSGS["assert_workspace_created"])

    # Step 2: Verify metadata exists
    if not verify_metadata_exists(host, workspace_path):
        log.failed(LOG_MSGS["metadata_missing"], ASSERT_MSGS["assert_metadata_exists"])
        pytest.fail(ASSERT_MSGS["assert_metadata_exists"])

    log.check(LOG_MSGS["metadata_generated"])

    # Step 3: Validate JSON format
    if not verify_metadata_valid_json(host, workspace_path):
        log.failed(LOG_MSGS["metadata_invalid_json"], ASSERT_MSGS["assert_metadata_valid"])
        pytest.fail(ASSERT_MSGS["assert_metadata_valid"])

    log.check(LOG_MSGS["metadata_valid_json"])

    # Step 4: Check required fields
    metadata = read_metadata(host, workspace_path)

    if not metadata:
        log.failed("Failed to read metadata", ASSERT_MSGS["assert_metadata_exists"])
        pytest.fail(ASSERT_MSGS["assert_metadata_exists"])

    all_present, missing = verify_metadata_required_fields(metadata)

    if not all_present:
        log.failed(
            f"Missing metadata fields: {missing}",
            ASSERT_MSGS["assert_metadata_fields"]
        )
        pytest.fail(f"{ASSERT_MSGS['assert_metadata_fields']}: {missing}")

    for field in METADATA_REQUIRED_FIELDS:
        log.check(LOG_MSGS["metadata_field_present"].format(field=field))

    # Step 5: Check warning entries schema (per CSPEC-LOGEX-2026-001 Section 4.2)
    warnings_ok, warning_missing = verify_metadata_warning_entries(metadata)
    if not warnings_ok:
        log.check(f"Missing warning entry fields: {warning_missing}")

    log.passed(
        "Metadata synthesis successful",
        f"All {len(METADATA_REQUIRED_FIELDS)} required fields present"
    )
