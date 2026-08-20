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
FVT — Bundle Construction, Hash, and Completion Output

Verifies that the bundle stage (bundle.yml) produces:
- A deterministically-named tarball: omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz
- Subdirectories for k8s/ and slurm/ containing per-node log directories
- A valid SHA256 hash matching the metadata.json tar_sha256 field
- A completion summary with workspace, bundle, SHA256, mode, and warnings

Tests:
    TC-F04  Bundle Construction with Deterministic Naming
    TC-F05  Integrity Hash Generation
    TC-F06  User-Facing Completion Output
"""

import pytest
from omnia_auto import TestLogger

from library.vars import TEST_CASES as TC
from library.functions.log_collector_func import (
    compute_sha256,
    get_bundle_path,
    get_workspace_directory,
    list_bundle_contents,
    parse_collect_ini,
    read_metadata,
    verify_bundle_contains_node_logs,
    verify_bundle_contains_subdirs,
    verify_bundle_created,
    verify_bundle_name_format,
    verify_completion_summary,
    verify_hash_format,
    verify_hash_match,
)
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# ── Shared fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def workspace(host):
    """Locate the most recent workspace run folder."""
    return get_workspace_directory(host)


@pytest.fixture(scope="module")
def bundle_path(host):
    """Locate the most recent bundle archive."""
    return get_bundle_path(host)


@pytest.fixture(scope="module")
def parsed_inventory(host):
    """Parse collect.ini for node verification."""
    return parse_collect_ini(host)


# ── TC-F04: Bundle Construction with Deterministic Naming ───────────────────

@pytest.mark.order(4)
@pytest.mark.functional
class TestBundleConstruction:
    """TC-F04 — Verify bundle is created with correct naming and contents."""

    def test_bundle_exists(self, host, bundle_path):
        """Verify the tar.gz bundle was created."""
        tc = TC["bundle_construction"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying bundle archive exists ...")
        exists, path = verify_bundle_created(host)

        if exists:
            tl.passed(LOG["bundle_ok"], f"Bundle: {path}")
        else:
            tl.failed(LOG["bundle_failed"], "No bundle archive found")
            assert False, ASSERT["bundle_not_created"].format(
                detail="tar.gz bundle not found in output directory"
            )

    def test_bundle_name_format(self, host, bundle_path):
        """Verify bundle name matches omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz."""
        tc = TC["bundle_construction"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying bundle name format ...")
        assert bundle_path, "No bundle path"

        valid = verify_bundle_name_format(bundle_path)
        if valid:
            tl.passed(LOG["bundle_ok"], f"Format valid: {bundle_path}")
        else:
            tl.failed(LOG["bundle_failed"], f"Invalid name: {bundle_path}")
            assert False, ASSERT["bundle_not_created"].format(
                detail=f"Bundle name does not match expected format: {bundle_path}"
            )

    def test_bundle_contains_log_subdirs(self, host, bundle_path, parsed_inventory):
        """Verify bundle contains k8s/ and/or slurm/ subdirectories."""
        tc = TC["bundle_construction"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking bundle subdirectories ...")
        assert bundle_path, "No bundle path"

        subdirs = verify_bundle_contains_subdirs(host, bundle_path)
        has_k8s_nodes = any(
            parsed_inventory.get(s) for s in ["k8s_control_node", "k8s_worker_node"]
        )
        has_slurm_nodes = any(
            parsed_inventory.get(s)
            for s in ["slurm_control_node", "slurm_node",
                      "login_node", "login_compiler_node"]
        )

        ok = True
        details = []
        if has_k8s_nodes and not subdirs.get("k8s"):
            ok = False
            details.append("k8s/ missing but k8s nodes configured")
        if has_slurm_nodes and not subdirs.get("slurm"):
            ok = False
            details.append("slurm/ missing but slurm nodes configured")

        if ok:
            tl.passed(LOG["bundle_ok"], f"Subdirs: {subdirs}")
        else:
            tl.failed(LOG["bundle_failed"], "; ".join(details))
            assert False, ASSERT["bundle_not_created"].format(
                detail="; ".join(details)
            )

    def test_bundle_contains_node_logs(self, host, bundle_path, parsed_inventory):
        """Verify bundle contains per-node directories for populated groups."""
        tc = TC["bundle_construction"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking per-node log directories in bundle ...")
        assert bundle_path, "No bundle path"

        node_results = verify_bundle_contains_node_logs(
            host, bundle_path, parsed_inventory
        )

        if not node_results:
            tl.passed(LOG["bundle_ok"], "No populated groups to verify")
            return

        all_found = all(node_results.values())
        if all_found:
            tl.passed(LOG["bundle_ok"],
                      f"All groups found: {list(node_results.keys())}")
        else:
            missing = [k for k, v in node_results.items() if not v]
            tl.failed(LOG["bundle_failed"],
                      f"Missing node dirs for: {missing}")
            assert False, ASSERT["bundle_not_created"].format(
                detail=f"Node log directories missing for groups: {missing}"
            )

    def test_bundle_nonempty(self, host, bundle_path):
        """Verify bundle archive is not empty."""
        tc = TC["bundle_construction"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying bundle is non-empty ...")
        assert bundle_path, "No bundle path"

        contents = list_bundle_contents(host, bundle_path)
        if len(contents) > 0:
            tl.passed(LOG["bundle_ok"], f"{len(contents)} entries in archive")
        else:
            tl.failed(LOG["bundle_failed"], "Archive is empty")
            assert False, ASSERT["bundle_not_created"].format(
                detail="tar.gz archive contains 0 entries"
            )


# ── TC-F05: Integrity Hash Generation ──────────────────────────────────────

@pytest.mark.order(5)
@pytest.mark.functional
class TestHashGeneration:
    """TC-F05 — Verify SHA256 hash is generated and matches the bundle."""

    def test_metadata_has_sha256(self, host, workspace):
        """Verify metadata.json contains a non-empty tar_sha256 field."""
        tc = TC["hash_generation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Reading tar_sha256 from metadata.json ...")
        assert workspace, "No workspace"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata"

        sha256 = metadata.get("tar_sha256", "")
        if sha256 and verify_hash_format(sha256):
            tl.passed(LOG["hash_ok"], f"SHA256: {sha256[:16]}...")
        else:
            tl.failed(LOG["hash_failed"], f"Invalid SHA256: '{sha256}'")
            assert False, ASSERT["hash_mismatch"].format(
                metadata_hash=sha256 or "(empty)",
                computed_hash="(not computed)",
                detail="tar_sha256 field empty or invalid format"
            )

    def test_hash_matches_bundle(self, host, workspace, bundle_path):
        """Verify SHA256 in metadata matches actual bundle checksum."""
        tc = TC["hash_generation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Computing SHA256 and comparing ...")
        assert workspace, "No workspace"
        assert bundle_path, "No bundle path"

        metadata = read_metadata(host, workspace)
        assert metadata, "Could not read metadata"

        metadata_hash = metadata.get("tar_sha256", "")
        computed_hash = compute_sha256(host, bundle_path) or ""

        if metadata_hash and computed_hash and verify_hash_match(
            metadata_hash, computed_hash
        ):
            tl.passed(LOG["hash_ok"], "Metadata hash matches bundle")
        else:
            tl.failed(LOG["hash_failed"],
                      f"Mismatch: meta={metadata_hash[:16]}... "
                      f"vs computed={computed_hash[:16]}...")
            assert False, ASSERT["hash_mismatch"].format(
                metadata_hash=metadata_hash,
                computed_hash=computed_hash,
                detail="SHA256 in metadata.json does not match "
                       "the actual bundle checksum"
            )


# ── TC-F06: User-Facing Completion Output ──────────────────────────────────

@pytest.mark.order(6)
@pytest.mark.functional
class TestCompletionOutput:
    """TC-F06 — Verify the completion summary block in playbook output."""

    @pytest.fixture(autouse=True, scope="class")
    def _run_collection(self, host, request):
        """Execute collection and store output for the class."""
        success, output, rc = execute_log_collection(host, mode="full")
        request.cls.output = output
        request.cls.success = success

    def test_completion_summary_present(self, host):
        """Verify 'OMNIA LOG COLLECTION COMPLETE' banner appears."""
        tc = TC["completion_output"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking for completion banner ...")
        if "OMNIA LOG COLLECTION COMPLETE" in self.output:
            tl.passed(LOG["output_ok"], "Completion banner present")
        else:
            tl.failed(LOG["output_failed"], "Banner not found")
            assert False, ASSERT["output_incomplete"].format(
                detail="'OMNIA LOG COLLECTION COMPLETE' not in output"
            )

    def test_completion_fields(self, host):
        """Verify completion summary contains workspace, bundle, SHA256."""
        tc = TC["completion_output"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Parsing completion summary fields ...")
        fields = verify_completion_summary(self.output)

        missing = [k for k, v in fields.items() if v is None]

        if not missing:
            tl.passed(LOG["output_ok"],
                      f"All fields present: {list(fields.keys())}")
        else:
            tl.failed(LOG["output_failed"],
                      f"Missing fields: {missing}")
            assert False, ASSERT["output_incomplete"].format(
                detail=f"Completion summary missing: {missing}"
            )

    def test_completion_sha256_format(self, host):
        """Verify SHA256 in completion summary is 64-char hex."""
        tc = TC["completion_output"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying SHA256 format in summary ...")
        fields = verify_completion_summary(self.output)
        sha = fields.get("sha256", "")

        if sha and verify_hash_format(sha):
            tl.passed(LOG["output_ok"], f"SHA256: {sha[:16]}...")
        else:
            tl.failed(LOG["output_failed"],
                      f"Invalid SHA256 in summary: '{sha}'")
            assert False, ASSERT["output_incomplete"].format(
                detail=f"SHA256 in completion summary invalid: '{sha}'"
            )
