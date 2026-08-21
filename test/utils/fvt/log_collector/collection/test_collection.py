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
FVT — Log Collection Invocation & Source Collection

Verifies that ``ansible-playbook playbooks/collect.yml`` reads the
``collect.ini`` inventory, parses all functional groups, builds
dynamic host entries, dispatches per-group log collection via SSH,
and accumulates warnings for missing sources.

Tests:
    TC-F01  One-Shot Collection Invocation
    TC-F02  Source Collection and Warning Accumulation
"""

import pytest
from omnia_auto import TestLogger

from library.vars import TEST_CASES as TC
from library.functions.log_collector_func import (
    execute_log_collection,
    parse_collect_ini,
    verify_collect_ini_exists,
    verify_collect_ini_sections,
    verify_collect_ini_has_nodes,
    verify_collection_started,
    verify_inventory_parsed,
    verify_workspace_created,
)
from library.messages import (
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def collection_result(host):
    """Run collect.yml once for the entire module; cache the result."""
    success, output, rc = execute_log_collection(host, mode="full")
    return {"success": success, "output": output, "rc": rc}


@pytest.fixture(scope="module")
def parsed_inventory(host):
    """Parse collect.ini and return the inventory dict."""
    return parse_collect_ini(host)


# ── TC-F01: One-Shot Collection Invocation ──────────────────────────────────

@pytest.mark.order(1)
@pytest.mark.functional
class TestCollectionInvocation:
    """TC-F01 — Verify one-shot collection invocation."""

    def test_collect_ini_exists(self, host):
        """Verify collect.ini exists on the OIM server."""
        tc = TC["collection_invocation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying collect.ini exists on OIM ...")
        exists = verify_collect_ini_exists(host)

        if exists:
            tl.passed(LOG["collection_started"], "collect.ini found")
        else:
            tl.failed(LOG["collection_failed"], "collect.ini not found")
            assert False, ASSERT["collection_not_started"].format(
                detail="collect.ini not found at expected path"
            )

    def test_collect_ini_sections(self, host, parsed_inventory):
        """Verify collect.ini contains all expected functional group sections."""
        tc = TC["collection_invocation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying collect.ini sections ...")
        all_present, missing = verify_collect_ini_sections(parsed_inventory)

        if all_present:
            tl.passed(LOG["collection_started"],
                      f"All {len(parsed_inventory)} sections present")
        else:
            tl.failed(LOG["collection_failed"],
                      f"Missing sections: {missing}")
            assert False, ASSERT["collection_not_started"].format(
                detail=f"Missing INI sections: {missing}"
            )

    def test_collect_ini_has_nodes(self, host, parsed_inventory):
        """Verify at least one section has node IPs defined."""
        tc = TC["collection_invocation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying collect.ini has populated groups ...")
        has_nodes, counts = verify_collect_ini_has_nodes(parsed_inventory)

        if has_nodes:
            populated = {k: v for k, v in counts.items() if v > 0}
            tl.passed(LOG["collection_started"],
                      f"Groups with nodes: {populated}")
        else:
            tl.failed(LOG["collection_failed"], "No nodes in any group")
            assert False, ASSERT["collection_not_started"].format(
                detail="collect.ini has no node IPs in any section"
            )

    @pytest.mark.requires_playbook
    def test_playbook_execution(self, host, collection_result):
        """Verify ansible-playbook collect.yml executes successfully."""
        tc = TC["collection_invocation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying playbook execution ...")
        output = collection_result["output"]
        started = verify_collection_started(output)

        if collection_result["success"] and started:
            tl.passed(LOG["collection_started"], "Playbook completed")
        else:
            tl.failed(LOG["collection_failed"],
                      f"rc={collection_result['rc']}")
            assert False, ASSERT["collection_not_started"].format(
                detail=f"Playbook exit code: {collection_result['rc']}"
            )

    @pytest.mark.requires_playbook
    def test_inventory_parsed(self, host, collection_result):
        """Verify the INI inventory was parsed during playbook execution."""
        tc = TC["collection_invocation"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying INI inventory parsing in output ...")
        parsed = verify_inventory_parsed(collection_result["output"])

        if parsed:
            tl.passed(LOG["collection_started"], "INI parsed")
        else:
            tl.failed(LOG["collection_failed"], "INI parse not found in output")
            assert False, ASSERT["collection_not_started"].format(
                detail="'Parse INI inventory file' task not found in output"
            )


# ── TC-F02: Source Collection and Warning Accumulation ──────────────────────

@pytest.mark.order(2)
@pytest.mark.functional
class TestSourceCollection:
    """TC-F02 — Verify source collection and warning accumulation."""

    @pytest.mark.requires_playbook
    def test_workspace_created(self, host, collection_result):
        """Verify workspace directory was created after collection."""
        tc = TC["source_collection"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Verifying workspace directory created ...")
        exists, workspace = verify_workspace_created(host)

        if exists:
            tl.passed(LOG["source_collected"], f"Workspace: {workspace}")
        else:
            tl.failed(LOG["source_failed"], "No workspace directory found")
            assert False, ASSERT["source_not_collected"].format(
                detail="Workspace directory not created after collection"
            )

    @pytest.mark.requires_playbook
    def test_warning_count_in_output(self, host, collection_result):
        """Verify warning count appears in completion summary."""
        tc = TC["source_collection"]
        tl = TestLogger(tc["title"], tc["id"])

        tl.check("Checking warning count in output ...")
        output = collection_result["output"]
        # The completion summary prints "Warnings : <N>"
        if "Warnings" in output or "OMNIA LOG COLLECTION COMPLETE" in output:
            tl.passed(LOG["source_collected"],
                      "Warning summary present in output")
        else:
            tl.failed(LOG["source_failed"],
                      "No completion summary in output")
            assert False, ASSERT["source_not_collected"].format(
                detail="Completion summary block not found in output"
            )
