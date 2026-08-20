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
Log Collector — Functions

Contains all helper functions for log collection verification tests.
Aligned with the developer implementation in
``src/utils/roles/log_collector/`` and ``src/utils/playbooks/collect.yml``.

The playbook reads ``collect.ini`` (INI format) to build a dynamic
inventory of nodes grouped by functional role, then collects logs
from each node via SSH and bundles them on the OIM server.

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from omnia_auto import run_on_host
from ..vars.common_vars import (
    BUNDLE_NAME_PATTERN,
    CMDS,
    COLLECT_INI_PATH,
    COLLECT_INI_SECTIONS,
    EXIT_CODES,
    INI_SECTION_TO_GROUP,
    LOG_COLLECTION_COMMAND,
    LOG_COLLECTION_CURATED_MODE,
    LOG_PATHS,
    LOG_ROOT,
    METADATA_REQUIRED_FIELDS,
    OUTPUT_PATHS,
    SHA256_CONFIG,
    STAGE_TO_SUBDIR,
    TEST_FILES,
    WARNING_ENTRY_FIELDS,
    WARNING_PATTERNS,
)


# =============================================================================
# COLLECT.INI PARSING & INVENTORY FUNCTIONS
# =============================================================================

def parse_collect_ini(host, ini_path: str = "") -> Dict[str, List[str]]:
    """
    Parse collect.ini on the OIM server and return the inventory dict.

    Uses the same Python configparser logic as prepare.yml.

    Args:
        host: Testinfra host object (OIM connection)
        ini_path: Path to collect.ini (default: COLLECT_INI_PATH)

    Returns:
        Dict mapping section names to lists of IP addresses.
        Empty dict on failure.
    """
    path = ini_path or COLLECT_INI_PATH
    cmd = CMDS["validate_ini_parse"].format(ini_path=path)
    result = run_on_host(host, cmd)

    if result.rc == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {}
    return {}


def verify_collect_ini_exists(host, ini_path: str = "") -> bool:
    """
    Verify that collect.ini exists on the OIM server.

    Args:
        host: Testinfra host object
        ini_path: Path to collect.ini (default: COLLECT_INI_PATH)

    Returns:
        True if file exists, False otherwise
    """
    path = ini_path or COLLECT_INI_PATH
    cmd = CMDS["file_exists"].format(path=path)
    result = run_on_host(host, cmd)
    return "exists" in result.stdout


def verify_collect_ini_sections(inventory: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
    """
    Verify that collect.ini contains all expected sections.

    Args:
        inventory: Parsed inventory dict from parse_collect_ini()

    Returns:
        Tuple of (all_present, missing_sections)
    """
    missing = [s for s in COLLECT_INI_SECTIONS if s not in inventory]
    return len(missing) == 0, missing


def verify_collect_ini_has_nodes(inventory: Dict[str, List[str]]) -> Tuple[bool, Dict[str, int]]:
    """
    Verify that at least one section in collect.ini has node IPs.

    Args:
        inventory: Parsed inventory dict from parse_collect_ini()

    Returns:
        Tuple of (has_any_nodes, section_counts)
    """
    counts = {section: len(ips) for section, ips in inventory.items()}
    has_any = any(count > 0 for count in counts.values())
    return has_any, counts


def get_populated_groups(inventory: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Return only the groups that have at least one node IP.

    Args:
        inventory: Parsed inventory dict from parse_collect_ini()

    Returns:
        Dict of section_name -> [ip_list] for non-empty groups
    """
    return {section: ips for section, ips in inventory.items() if ips}


# =============================================================================
# COLLECTION EXECUTION FUNCTIONS
# =============================================================================

def execute_log_collection(host, mode: str = "full") -> Tuple[bool, str, int]:
    """
    Execute the log collection playbook on the OIM server.

    The playbook runs directly on the OIM host (not inside a container).
    It reads collect.ini, builds dynamic inventory, SSHes to each node
    to fetch logs, and bundles them locally.

    Args:
        host: Testinfra host object (OIM connection)
        mode: Collection mode - "full" or "curated_support"

    Returns:
        Tuple of (success, output, exit_code)
    """
    if mode == "curated_support":
        command = LOG_COLLECTION_CURATED_MODE
    else:
        command = LOG_COLLECTION_COMMAND

    result = run_on_host(host, command)

    success = result.rc in (EXIT_CODES["success"], EXIT_CODES["partial_success"])
    return success, result.stdout + result.stderr, result.rc


def verify_collection_started(output: str) -> bool:
    """
    Verify that collection pipeline started successfully.

    Checks for PLAY names that appear in ansible-playbook output
    matching the plays defined in collect.yml.

    Args:
        output: Command output string

    Returns:
        True if collection started, False otherwise
    """
    start_indicators = [
        "PLAY [Stage globals]",
        "PLAY [Prepare targets and inventory]",
        "PLAY [Collect k8s master logs]",
        "PLAY [Collect k8s worker logs]",
        "PLAY [Collect slurm controller logs]",
        "PLAY [Collect slurm node logs]",
        "PLAY [Collect login node logs]",
        "PLAY [Collect login compiler node logs]",
        "PLAY [Bundle collected logs and publish summary]",
        "OMNIA LOG COLLECTION COMPLETE",
    ]
    return any(indicator in output for indicator in start_indicators)


def verify_inventory_parsed(output: str) -> bool:
    """
    Verify that the INI inventory was parsed during playbook execution.

    Args:
        output: Ansible playbook output

    Returns:
        True if parse task completed, False otherwise
    """
    return "Parse INI inventory file" in output


def verify_dynamic_hosts_added(output: str, group: str) -> bool:
    """
    Verify dynamic hosts were added for a specific group.

    Args:
        output: Ansible playbook output
        group: Group name (e.g., "k8s masters", "slurm controllers")

    Returns:
        True if add_host task ran for the group
    """
    pattern = f"Add dynamic hosts for {group}"
    return pattern in output


def check_target_connectivity(host) -> Dict[str, Any]:
    """Check target host connectivity.

    Returns:
        Dict with 'success' and 'error' keys.
    """
    cmd = CMDS["echo_test"]
    result = run_on_host(host, cmd)
    if result.rc == 0 and "connectivity_ok" in result.stdout:
        return {"success": True, "error": ""}
    return {
        "success": False,
        "error": f"Connectivity check failed (rc={result.rc})",
    }


# =============================================================================
# WORKSPACE FUNCTIONS
# =============================================================================

def get_workspace_directory(host) -> Optional[str]:
    """
    Find the most recent workspace directory (bundle directory) on OIM.

    Args:
        host: Testinfra host object

    Returns:
        Workspace directory path or None if not found
    """
    output_root = OUTPUT_PATHS['default_output_root']
    dir_pattern = OUTPUT_PATHS['bundle_dir_pattern']
    cmd = CMDS["find_workspace"].format(
        output_root=output_root,
        dir_pattern=dir_pattern,
    )
    result = run_on_host(host, cmd)

    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def verify_workspace_created(host) -> Tuple[bool, Optional[str]]:
    """
    Verify workspace directory was created on OIM.

    Args:
        host: Testinfra host object

    Returns:
        Tuple of (exists, workspace_path)
    """
    workspace = get_workspace_directory(host)
    if workspace:
        cmd = CMDS["dir_exists"].format(path=workspace)
        result = run_on_host(host, cmd)
        return "exists" in result.stdout, workspace
    return False, None


def verify_workspace_subdirs(host, workspace_path: str) -> Dict[str, bool]:
    """
    Verify k8s/ and slurm/ subdirectories were created in workspace.

    These are the intermediate collection directories before bundling.
    After bundling, they are moved into the run folder and then removed.

    Args:
        host: Testinfra host object
        workspace_path: Path to the workspace directory

    Returns:
        Dict of subdir_name -> exists (True/False)
    """
    result = {}
    for subdir in ["k8s", "slurm"]:
        path = f"{workspace_path}/{subdir}"
        cmd = CMDS["dir_exists"].format(path=path)
        r = run_on_host(host, cmd)
        result[subdir] = "exists" in r.stdout
    return result


# =============================================================================
# BUNDLE FUNCTIONS
# =============================================================================

def get_bundle_path(host) -> Optional[str]:
    """
    Find the most recent bundle archive on OIM.

    Args:
        host: Testinfra host object

    Returns:
        Bundle file path or None if not found
    """
    output_root = OUTPUT_PATHS['default_output_root']
    cmd = CMDS["find_bundle"].format(output_root=output_root)
    result = run_on_host(host, cmd)

    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def verify_bundle_created(host) -> Tuple[bool, Optional[str]]:
    """
    Verify bundle archive was created on OIM.

    Args:
        host: Testinfra host object

    Returns:
        Tuple of (exists, bundle_path)
    """
    bundle = get_bundle_path(host)
    if bundle:
        cmd = CMDS["file_exists"].format(path=bundle)
        result = run_on_host(host, cmd)
        return "exists" in result.stdout, bundle
    return False, None


def verify_bundle_name_format(bundle_path: str) -> bool:
    """
    Verify bundle filename matches expected format.

    Format: omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz

    Args:
        bundle_path: Full path to bundle file

    Returns:
        True if format matches, False otherwise
    """
    filename = os.path.basename(bundle_path)
    return bool(re.match(BUNDLE_NAME_PATTERN, filename))


def extract_bundle(host, bundle_path: str, extract_dir: str) -> bool:
    """
    Extract bundle archive to directory on OIM.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        extract_dir: Directory to extract to

    Returns:
        True if extraction successful, False otherwise
    """
    run_on_host(host, f"mkdir -p {extract_dir}")

    cmd = CMDS["extract_archive"].format(
        archive_path=bundle_path,
        extract_dir=extract_dir,
    )
    result = run_on_host(host, cmd)
    return result.rc == 0


def list_bundle_contents(host, bundle_path: str) -> List[str]:
    """
    List contents of bundle archive.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive

    Returns:
        List of file paths in archive
    """
    cmd = CMDS["list_archive"].format(archive_path=bundle_path)
    result = run_on_host(host, cmd)

    if result.rc == 0:
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    return []


def verify_bundle_contains_subdirs(host, bundle_path: str) -> Dict[str, bool]:
    """
    Verify bundle archive contains k8s/ and/or slurm/ subdirectories.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive

    Returns:
        Dict of subdir -> present_in_archive
    """
    contents = list_bundle_contents(host, bundle_path)
    return {
        "k8s": any("k8s/" in item for item in contents),
        "slurm": any("slurm/" in item for item in contents),
    }


def verify_bundle_contains_node_logs(
    host, bundle_path: str, inventory: Dict[str, List[str]]
) -> Dict[str, bool]:
    """
    Verify bundle contains log directories for nodes from the inventory.

    The naming pattern is: <subdir>/<hostname>_<timestamp>/
    where hostname is like k8s_master_10_45_2_105.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        inventory: Parsed collect.ini inventory

    Returns:
        Dict of section_name -> found_in_bundle
    """
    contents = list_bundle_contents(host, bundle_path)
    result = {}

    for section, ips in inventory.items():
        if not ips:
            continue
        # Check if any IP (with dots replaced by underscores) appears in contents
        found = False
        for ip in ips:
            ip_underscored = ip.replace(".", "_")
            if any(ip_underscored in item for item in contents):
                found = True
                break
        result[section] = found

    return result


# =============================================================================
# METADATA FUNCTIONS
# =============================================================================

def read_metadata(host, workspace_path: str) -> Optional[Dict[str, Any]]:
    """
    Read and parse metadata JSON from workspace on OIM.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory

    Returns:
        Parsed metadata dict or None if not found/invalid
    """
    cmd = CMDS["read_metadata"].format(workspace=workspace_path)
    result = run_on_host(host, cmd)

    if result.rc == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
    return None


def verify_metadata_exists(host, workspace_path: str) -> bool:
    """
    Verify metadata JSON file exists in workspace.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory

    Returns:
        True if metadata exists, False otherwise
    """
    metadata_path = f"{workspace_path}/{OUTPUT_PATHS['metadata_filename']}"
    cmd = CMDS["file_exists"].format(path=metadata_path)
    result = run_on_host(host, cmd)
    return "exists" in result.stdout


def verify_metadata_valid_json(host, workspace_path: str) -> bool:
    """
    Verify metadata is valid JSON format.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory

    Returns:
        True if valid JSON, False otherwise
    """
    metadata_path = f"{workspace_path}/{OUTPUT_PATHS['metadata_filename']}"
    cmd = CMDS["validate_json"].format(file_path=metadata_path)
    result = run_on_host(host, cmd)
    return result.rc == 0


def verify_metadata_required_fields(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify metadata contains all required fields from metadata.json.j2.

    Args:
        metadata: Parsed metadata dictionary

    Returns:
        Tuple of (all_present, missing_fields)
    """
    missing = [f for f in METADATA_REQUIRED_FIELDS if f not in metadata]
    return len(missing) == 0, missing


def verify_metadata_collection_mode(metadata: Dict[str, Any], expected_mode: str) -> bool:
    """
    Verify the collection_mode field in metadata.

    Expected values: "complete logs" (default) or "curated_support".

    Args:
        metadata: Parsed metadata dictionary
        expected_mode: Expected collection mode string

    Returns:
        True if mode matches
    """
    return metadata.get("collection_mode") == expected_mode


def verify_metadata_warning_entries(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify warning entries in metadata contain required fields.

    Args:
        metadata: Parsed metadata dictionary

    Returns:
        Tuple of (all_valid, missing_fields)
    """
    warnings = metadata.get("warnings", [])
    if not warnings:
        return True, []

    missing = []
    for idx, warning in enumerate(warnings):
        for field in WARNING_ENTRY_FIELDS:
            if field not in warning:
                missing.append(f"warnings[{idx}].{field}")
    return len(missing) == 0, missing


def verify_warning_message_format(warning: Dict[str, Any]) -> bool:
    """
    Verify warning message follows the format from the role's rescue blocks.

    Expected format includes node name, node IP, and stage info.

    Args:
        warning: Warning entry dictionary

    Returns:
        True if format contains expected elements
    """
    message = warning.get("message", "")
    node_name = warning.get("node_name", "")

    return (
        node_name in message
        and ("not reachable" in message
             or "unreachable" in message
             or "missing" in message.lower()
             or "Collection task failed" in message)
    )


# =============================================================================
# HASH FUNCTIONS
# =============================================================================

def compute_sha256(host, file_path: str) -> Optional[str]:
    """
    Compute SHA256 hash of a file on OIM.

    Args:
        host: Testinfra host object
        file_path: Path to file

    Returns:
        SHA256 hash string or None if failed
    """
    cmd = CMDS["compute_sha256"].format(file_path=file_path)
    result = run_on_host(host, cmd)

    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def verify_hash_format(hash_value: str) -> bool:
    """
    Verify hash is valid SHA256 format (64-character hex).

    Args:
        hash_value: Hash string to verify

    Returns:
        True if valid format, False otherwise
    """
    return bool(re.match(r'^[a-fA-F0-9]{64}$', hash_value))


def verify_hash_in_output(output: str) -> Optional[str]:
    """
    Extract SHA256 hash from playbook completion output.

    Looks for the "SHA256" line in the completion summary block.

    Args:
        output: Ansible playbook output

    Returns:
        Hash value if found, None otherwise
    """
    match = re.search(SHA256_CONFIG["hash_pattern"], output)
    if match:
        return match.group(1)
    return None


def verify_hash_match(hash1: str, hash2: str) -> bool:
    """Compare two hash values (case-insensitive)."""
    return hash1.lower() == hash2.lower()


# =============================================================================
# OUTPUT VERIFICATION FUNCTIONS
# =============================================================================

def verify_completion_summary(output: str) -> Dict[str, Optional[str]]:
    """
    Parse the completion summary block from playbook output.

    The bundle.yml completion task prints a structured summary with
    workspace, run folder, bundle path, metadata path, SHA256, mode,
    and warning count.

    Args:
        output: Ansible playbook output

    Returns:
        Dict of extracted fields (None if not found)
    """
    fields = {}
    patterns = {
        "workspace": r"Collected Workspace\s*:\s*(\S+)",
        "run_folder": r"Run Folder\s*:\s*(\S+)",
        "bundle_path": r"Bundle Path\s*:\s*(\S+)",
        "metadata_path": r"Metadata Path\s*:\s*(\S+)",
        "sha256": r"SHA256\s*:\s*([a-fA-F0-9]{64})",
        "collection_mode": r"Collection Mode\s*:\s*(.+?)(?:\s*$|\s*\")",
        "warnings": r"Warnings?\s*:\s*(\d+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        fields[key] = match.group(1).strip() if match else None
    return fields


def verify_path_is_absolute(path: str) -> bool:
    """Verify path is absolute (starts with /)."""
    return path.startswith("/")


def verify_warning_summary_in_output(output: str) -> Tuple[bool, int]:
    """
    Verify warning summary is present in completion output.

    Args:
        output: Ansible playbook output

    Returns:
        Tuple of (found, warning_count)
    """
    pattern = r"Warnings?\s*:\s*(\d+)"
    match = re.search(pattern, output, re.IGNORECASE)
    if match:
        return True, int(match.group(1))
    return False, 0


# =============================================================================
# ERROR & WARNING FUNCTIONS
# =============================================================================

def set_directory_permissions(host, path: str, mode: str) -> bool:
    """Set permissions on a directory on OIM."""
    cmd = CMDS["set_permissions"].format(mode=mode, path=path)
    result = run_on_host(host, cmd)
    return result.rc == 0


def verify_not_writable_error(output: str) -> bool:
    """Verify output contains permission/writable error."""
    return bool(re.search(WARNING_PATTERNS["output_not_writable"], output))


def verify_archive_failure_error(output: str) -> bool:
    """Verify output contains archive failure error."""
    return (
        bool(re.search(WARNING_PATTERNS["archive_failure"], output))
        or bool(re.search(WARNING_PATTERNS["disk_full"], output))
    )


def verify_unreachable_node_warning(output: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify output contains unreachable node warning with hostname and IP.

    Args:
        output: Ansible playbook output

    Returns:
        Tuple of (found, hostname, ip)
    """
    match = re.search(WARNING_PATTERNS["unreachable_node"], output)
    if match:
        return True, match.group(1), match.group(2)
    return False, None, None


def verify_missing_source_warning(output: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify output contains missing source file/directory warning.

    Args:
        output: Ansible playbook output

    Returns:
        Tuple of (found, source_path, node_name)
    """
    match = re.search(WARNING_PATTERNS["missing_source"], output)
    if match:
        return True, match.group(1), match.group(2)
    return False, None, None


def find_ssh_failure_markers(host) -> List[str]:
    """
    Find SSH_COLLECTION_FAILED.txt marker files in the output directory.

    These are created by bundle.yml for unreachable/failed nodes.

    Args:
        host: Testinfra host object

    Returns:
        List of marker file paths
    """
    output_root = OUTPUT_PATHS["default_output_root"]
    cmd = CMDS["find_failure_markers"].format(output_root=output_root)
    result = run_on_host(host, cmd)

    if result.rc == 0 and result.stdout.strip():
        return [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
    return []


# =============================================================================
# TEST FILE MANAGEMENT FUNCTIONS
# =============================================================================

def create_temp_test_files(host) -> bool:
    """Create temporary test files for compatibility tests."""
    for path in TEST_FILES["temp_files"]:
        cmd = CMDS["create_temp_file"].format(path=path)
        result = run_on_host(host, cmd)
        if result.rc != 0:
            return False
    return True


def create_stale_test_file(host) -> bool:
    """Create stale test file with old timestamp."""
    cmd = CMDS["create_stale_file"].format(
        days=TEST_FILES["stale_age_days"],
        path=TEST_FILES["stale_log"],
    )
    result = run_on_host(host, cmd)
    return result.rc == 0


def cleanup_test_files(host) -> bool:
    """Remove test files created during tests."""
    all_files = TEST_FILES["temp_files"] + [TEST_FILES["stale_log"]]
    for path in all_files:
        cmd = CMDS["remove_file"].format(path=path)
        run_on_host(host, cmd)
    return True


def fill_disk_space(host, path: str, size_mb: int) -> bool:
    """Fill disk space with dummy file (for error testing)."""
    cmd = CMDS["fill_disk"].format(path=path, size_mb=size_mb)
    run_on_host(host, cmd)
    return True  # dd may return non-zero on disk full, which is expected


def free_disk_space(host, path: str) -> bool:
    """Remove fill file to free disk space."""
    cmd = CMDS["free_disk"].format(path=path)
    result = run_on_host(host, cmd)
    return result.rc == 0


# =============================================================================
# IDEMPOTENCY FUNCTIONS
# =============================================================================

def get_bundle_content_checksum(host, bundle_path: str) -> Optional[str]:
    """
    Get checksum of bundle contents (excluding metadata timestamp).

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive

    Returns:
        Checksum string or None if failed
    """
    extract_dir = "/tmp/bundle_check_" + str(int(time.time()))
    if not extract_bundle(host, bundle_path, extract_dir):
        return None

    cmd = CMDS["content_checksum"].format(dir_path=extract_dir)
    result = run_on_host(host, cmd)

    # Cleanup
    run_on_host(host, CMDS["rm_dir"].format(path=extract_dir))

    if result.rc == 0:
        return result.stdout.strip().split()[0]
    return None


def compare_bundle_contents(
    host,
    bundle1_path: str,
    bundle2_path: str,
) -> Tuple[bool, str, str]:
    """
    Compare contents of two bundles (excluding metadata timestamp).

    Args:
        host: Testinfra host object
        bundle1_path: Path to first bundle
        bundle2_path: Path to second bundle

    Returns:
        Tuple of (identical, checksum1, checksum2)
    """
    checksum1 = get_bundle_content_checksum(host, bundle1_path)
    checksum2 = get_bundle_content_checksum(host, bundle2_path)

    if checksum1 and checksum2:
        return checksum1 == checksum2, checksum1, checksum2
    return False, checksum1 or "", checksum2 or ""


# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

def cleanup_workspace(host, workspace_path: str) -> bool:
    """Remove workspace directory on OIM."""
    cmd = CMDS["rm_dir"].format(path=workspace_path)
    result = run_on_host(host, cmd)
    return result.rc == 0


def cleanup_bundle(host, bundle_path: str) -> bool:
    """Remove bundle archive on OIM."""
    cmd = CMDS["rm_file"].format(path=bundle_path)
    result = run_on_host(host, cmd)
    return result.rc == 0
