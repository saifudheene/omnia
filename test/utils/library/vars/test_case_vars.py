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
Utils (Log Collector) — Test Case Registry.

Central registry mapping every test to its TC ID and title.
Test files reference ``TEST_CASES["key"]`` to get a consistent
test-case identifier and display name.

Usage in test files::

    from library.vars import TEST_CASES as TC

    tc = TC["deploy_collect"]
    tl = TestLogger(tc["title"], tc["id"])
"""

TEST_CASES = {
    # ── Deploy ────────────────────────────────────────────────────────────
    "deploy_collect": {
        "id": "TC-F00",
        "title": "Deploy collect.yml (full mode)",
    },

    # ── Functional — Collection ───────────────────────────────────────────
    "collection_invocation": {
        "id": "TC-F01",
        "title": "One-Shot Collection Invocation",
    },
    "source_collection": {
        "id": "TC-F02",
        "title": "Source Collection and Warning Accumulation",
    },

    # ── Functional — Metadata ─────────────────────────────────────────────
    "metadata_synthesis": {
        "id": "TC-F03",
        "title": "Metadata Synthesis and Inclusion",
    },

    # ── Functional — Bundle ───────────────────────────────────────────────
    "bundle_construction": {
        "id": "TC-F04",
        "title": "Bundle Construction with Deterministic Naming",
    },
    "hash_generation": {
        "id": "TC-F05",
        "title": "Integrity Hash Generation",
    },
    "completion_output": {
        "id": "TC-F06",
        "title": "User-Facing Completion Output",
    },

    # ── Negative / Error ──────────────────────────────────────────────────
    "output_not_writable": {
        "id": "TC-E01",
        "title": "Output Directory Not Writable",
    },
    "missing_sources": {
        "id": "TC-E03",
        "title": "Missing Source Files — Warning Emitted",
    },
    "archive_failure": {
        "id": "TC-E04",
        "title": "Archive Generation Failure",
    },

    # ── Compatibility ─────────────────────────────────────────────────────
    "curated_mode": {
        "id": "TC-C01",
        "title": "Curated Support Mode — Exclude Temporary/Stale Logs",
    },
    "full_mode": {
        "id": "TC-C02",
        "title": "Full Collection Mode — Include All Logs",
    },

    # ── NFT — Idempotency ─────────────────────────────────────────────────
    "idempotency": {
        "id": "TC-I01",
        "title": "Collection Command Idempotency",
    },
}
