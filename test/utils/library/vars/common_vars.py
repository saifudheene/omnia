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
Utils — Module-Specific Variables

Common vars (ssh_opts, config names, timeouts) live in the
``omnia_auto`` package and are set via ``omnia_auto.configure()``
in conftest.py.

Only module-specific constants remain here.

Reference Specs:
- BSPEC-LOGEX-2026-001 (Behavior Specification)
- CSPEC-LOGEX-2026-001 (Component Specification)
"""

import os
import re
from typing import Dict

# =============================================================================
# DIRECTORY PATHS
# =============================================================================

# Module root: test/utils/ directory (where conftest.py lives)
MODULE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))

# Parent of module root: test/
TEST_ROOT = os.path.dirname(MODULE_ROOT)

# Omnia monorepo root: omnia/
MONOREPO_ROOT = os.path.dirname(TEST_ROOT)

# src/ paths — used when dataset is empty (default: use src/ directly)
SRC_INPUT_DIR = os.path.join(
    MONOREPO_ROOT, "src", "utils", "input",
)

# =============================================================================
# DOMAIN IDENTITY
# =============================================================================

DOMAIN_NAME = "utils"
CONTAINER_NAME = "omnia_core"

# Environment variable names on the target host
ENV_OMNIA_DATA_PATH = "OMNIA_DATA_PATH"
ENV_OMNIA_PROJECT_NAME = "OMNIA_PROJECT_NAME"

# =============================================================================
# PLAYBOOK CONFIGURATION (module-specific)
# =============================================================================

# Playbook entry point (relative to playbooks/)
PLAYBOOK_ENTRY_POINT = "collect.yml"
PLAYBOOK_WORKDIR = "src/utils/playbooks"

# Valid playbook tags
PLAYBOOK_TAGS = [
    "collect",
]

# =============================================================================
# COMMAND CONFIGURATION (inside omnia_core container)
# =============================================================================

# Default mode (full collection scope)
LOG_COLLECTION_COMMAND = (
    "cd /omnia/src/utils/playbooks && ansible-playbook collect.yml"
)

# Curated support mode (exclude temporary/stale-old logs)
LOG_COLLECTION_CURATED_MODE = (
    "cd /omnia/src/utils/playbooks && ansible-playbook collect.yml"
    " -e collection_mode=curated_support"
)

# Playbook path (inside omnia_core container)
COLLECT_PLAYBOOK_PATH = "/omnia/src/utils/playbooks/collect.yml"

# =============================================================================
# BUNDLE NAMING PATTERN
# =============================================================================

BUNDLE_NAME_PATTERN = r"omnia_logs_(?P<timestamp>\d{8}-\d{6})\.tar\.gz"
BUNDLE_NAME_FORMAT = "omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz"

# =============================================================================
# OUTPUT PATHS
# =============================================================================

OUTPUT_PATHS = {
    "default_output_root": "/opt/omnia/collector_logs",
    "workspace_prefix": "omnia_logs_",
    "bundle_extension": ".tar.gz",
    "metadata_filename": "metadata.json",
    "bundle_dir_pattern": "omnia_logs_*",
}

# =============================================================================
# METADATA FIELDS (per CSPEC-LOGEX-2026-001 Section 4)
# =============================================================================

METADATA_REQUIRED_FIELDS = [
    "bundle_name",
    "tar_relative_path",
    "tar_sha256",
    "bundle_generated_at_utc",
    "bundle_generated_at_local",
    "trigger_user",
    "oim_host_os",
    "identifier",
    "collection_mode",
    "exclusions_applied",
    "warning_count",
    "warnings",
]

# Warning Entry Schema (per CSPEC-LOGEX-2026-001 Section 4.2)
WARNING_ENTRY_FIELDS = [
    "source",
    "node_name",
    "node_ip",
    "reason",
    "message",
    "timestamp",
]

# =============================================================================
# LOG SOURCES
# =============================================================================

LOG_SOURCES = {
    "kubernetes": {
        "description": "Kubernetes cluster logs",
        "sources": ["pod_logs", "node_logs", "system_logs"],
    },
    "slurm": {
        "description": "Slurm workload manager logs",
        "sources": ["job_logs", "scheduler_logs", "node_logs"],
    },
}

# =============================================================================
# COLLECTION MODES
# =============================================================================

COLLECTION_MODES = {
    "full": {
        "description": "Include all available logs including temporary and stale files",
        "excludes_temp": False,
        "excludes_stale": False,
        "extra_vars": None,
    },
    "curated_support": {
        "description": "Exclude temporary files and stale/old logs",
        "excludes_temp": True,
        "excludes_stale": True,
        "extra_vars": "collection_mode=curated_support",
        "exclusion_patterns": [
            "*.tmp", "*.temp", "*.bak", "*.gz", "*.bz2",
            "*.1", "*.2", "*.3", "*.4", "*.5",
        ],
    },
}

# =============================================================================
# TEST FILE PATTERNS (compatibility tests)
# =============================================================================

TEST_FILES = {
    "temp_files": [
        "/tmp/test.tmp",
        "/var/log/test.swp",
    ],
    "stale_log": "/var/log/old.log",
    "stale_age_days": 60,
}

# =============================================================================
# SHA256 CONFIGURATION
# =============================================================================

SHA256_CONFIG = {
    "hash_length": 64,
    "hash_pattern": r"SHA256\s*:\s*([a-fA-F0-9]{64})",
    "compute_command": "sha256sum {bundle_path}",
    "max_compute_time_seconds": 120,
}

# =============================================================================
# TIMEOUTS
# =============================================================================

TIMEOUTS = {
    "collection_start": 30,
    "collection_complete": 600,
    "hash_generation": 120,
    "ssh_connect": 30,
    "command_execution": 300,
}

# =============================================================================
# EXIT CODES
# =============================================================================

EXIT_CODES = {
    "success": 0,
    "partial_success": 1,
    "failure": 2,
    "permission_error": 126,
    "not_found": 127,
}

# =============================================================================
# WARNING PATTERNS
# =============================================================================

WARNING_PATTERNS = {
    "unreachable_node": (
        r"Node\s+(\S+)\s+\(([0-9.]+)\)\s+unreachable;"
        r"\s+continuing\s+collection\s+for\s+remaining\s+nodes"
    ),
    "missing_source": r"Source file\s+(\S+)\s+not found on node\s+(\S+)",
    "output_not_writable": r"Output directory not writable:\s+(\S+)",
    "archive_failure": r"Archive generation failed:\s+(.+)",
    "disk_full": r"No space left on device",
}

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

TEST_CONFIG = {
    "idempotency_wait_seconds": 5,
    "verify_archive_integrity": True,
    "cleanup_after_test": True,
}

# =============================================================================
# CONFIG VALIDATION CONSTANTS
# =============================================================================

IPV4_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
    r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

REQUIRED_CONFIG_FIELDS = [
    "project_name",
    "clone_path",
    "report_path",
    "report_name",
]

REQUIRED_DATASET_FILES = [
    "input/utils_config.yml",
]

REQUIRED_SRC_FILES: list = []

# =============================================================================
# CENTRALIZED SHELL COMMANDS
# =============================================================================
# All shell commands used by verification functions.
# Use .format() with named placeholders to fill in runtime values.

CMDS: Dict[str, str] = {
    # --- Collection ---
    "collect_logs": "{command}",
    "collect_logs_container": (
        "podman exec {container} bash -c '{command}'"
    ),

    # --- Workspace / Bundle ---
    "find_workspace": (
        "podman exec {container} bash -c "
        "'ls -td {output_root}/{dir_pattern} 2>/dev/null | head -1'"
    ),
    "find_bundle": (
        "podman exec {container} bash -c "
        "'ls -t {output_root}/omnia_logs_*/*.tar.gz 2>/dev/null | head -1'"
    ),
    "dir_exists_container": (
        "podman exec {container} test -d {path} "
        "&& echo 'exists' || echo 'not_exists'"
    ),
    "file_exists_container": (
        "podman exec {container} test -f {path} "
        "&& echo 'exists' || echo 'not_exists'"
    ),

    # --- Metadata ---
    "read_metadata": (
        "podman exec {container} cat {workspace}/metadata.json"
    ),
    "validate_json_container": (
        "podman exec {container} python3 -c "
        "\"import json; json.load(open('{file_path}'))\""
    ),

    # --- Archive ---
    "list_archive": (
        "podman exec {container} tar -tzf {archive_path}"
    ),
    "extract_archive": (
        "podman exec {container} tar -xzf {archive_path} -C {extract_dir}"
    ),

    # --- SHA256 ---
    "compute_sha256": (
        "podman exec {container} sha256sum {file_path} | awk '{{print $1}}'"
    ),

    # --- Permissions / Disk ---
    "set_permissions": (
        "podman exec {container} chmod {mode} {path}"
    ),
    "check_writable": (
        "podman exec {container} bash -c "
        "\"test -w {path} && echo 'writable' || echo 'not_writable'\""
    ),
    "fill_disk": (
        "podman exec {container} bash -c "
        "'dd if=/dev/zero of={path}/fillfile bs=1M count={size_mb} "
        "2>/dev/null || true'"
    ),
    "free_disk": (
        "podman exec {container} rm -f {path}/fillfile"
    ),

    # --- Test file management ---
    "create_temp_file": "podman exec {container} touch {path}",
    "create_stale_file": (
        "podman exec {container} bash -c "
        "\"touch -d '{days} days ago' {path}\""
    ),
    "remove_file": "podman exec {container} rm -f {path}",

    # --- Cleanup ---
    "rm_dir": "podman exec {container} rm -rf {path}",
    "rm_file": "podman exec {container} rm -f {path}",

    # --- Content checksum ---
    "content_checksum": (
        "podman exec {container} bash -c "
        "\"find {dir_path} -type f ! -name 'metadata.json' "
        "-exec md5sum {{}} \\; | sort | md5sum\""
    ),

    # --- System ---
    "echo_test": "echo connectivity_ok 2>/dev/null",
    "file_exists": "test -f {path} && echo exists",
    "dir_exists": "test -d {path} && echo exists",
    "cat_file": "cat {path} 2>/dev/null",
}
