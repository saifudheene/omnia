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

"""Log Collector — Variables package."""

from .log_collector_vars import (
    LOG_COLLECTION_COMMAND,
    LOG_COLLECTION_CURATED_MODE,
    COLLECT_PLAYBOOK_PATH,
    BUNDLE_NAME_PATTERN,
    OUTPUT_PATHS,
    METADATA_REQUIRED_FIELDS,
    WARNING_ENTRY_FIELDS,
    COLLECTION_MODES,
    SHA256_CONFIG,
    TIMEOUTS,
    EXIT_CODES,
    WARNING_PATTERNS,
    CMD_TEMPLATES,
    TEST_CONFIG,
    TEST_FILES,
    PLAYBOOK_ENTRY_POINT,
    PLAYBOOK_WORKDIR,
    DOMAIN_NAME,
    CONTAINER_NAME,
)

# Test-case IDs used by conftest.py for summary table
TEST_CASES = {
    "tcf01_collection_invocation": {"id": "TC-F01"},
    "tcf02_source_collection":     {"id": "TC-F02"},
    "tcf03_metadata_synthesis":    {"id": "TC-F03"},
    "tcf04_bundle_construction":   {"id": "TC-F04"},
    "tcf05_hash_generation":       {"id": "TC-F05"},
    "tcf06_completion_output":     {"id": "TC-F06"},
    "tce01_output_not_writable":   {"id": "TC-E01"},
    "tce03_missing_sources":       {"id": "TC-E03"},
    "tce04_archive_failure":       {"id": "TC-E04"},
    "tci01_idempotency":           {"id": "TC-I01"},
    "tcc01_curated_mode":          {"id": "TC-C01"},
    "tcc02_full_mode":             {"id": "TC-C02"},
}
