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

Constants aligned with the developer implementation in
``src/utils/roles/log_collector/`` and ``src/utils/playbooks/collect.yml``.

The playbook reads ``collect.ini`` (INI format with functional groups)
and dispatches log collection to nodes per group.

Reference Specs:
- BSPEC-LOGEX-2026-001 (Behavior Specification)
- CSPEC-LOGEX-2026-001 (Component Specification)
"""

import os
import re
from typing import Dict, List

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
# PLAYBOOK CONFIGURATION (aligned with src/utils/playbooks/collect.yml)
# =============================================================================

# Playbook entry point (relative to src/utils/)
PLAYBOOK_ENTRY_POINT = "collect.yml"
PLAYBOOK_WORKDIR = "src/utils"

# Valid playbook tags (from collect.yml plays)
PLAYBOOK_TAGS = [
    "setup",
    "prepare",
    "k8s",
    "slurm",
    "bundle",
    "curated_support",
    "always",
]

# Playbook stages dispatched via the 'stage' variable
PLAYBOOK_STAGES = [
    "setup",
    "prepare",
    "k8s_master",
    "k8s_worker",
    "slurm_ctl",
    "slurm_node",
    "login_node",
    "login_compiler_node",
    "bundle",
]

# =============================================================================
# COLLECT.INI — NODE INVENTORY (aligned with src/utils/input/collect.ini)
# =============================================================================

# Path to the INI inventory file on the OIM server
COLLECT_INI_PATH = "/opt/omnia/utils/input/project_default/collect.ini"

# Source INI file in the repo (before omnia.sh --init copies it)
COLLECT_INI_SRC = os.path.join(SRC_INPUT_DIR, "collect.ini")

# Supported functional group sections in collect.ini
# These map to the [section_name] entries in the INI file
COLLECT_INI_SECTIONS = [
    "slurm_control_node",
    "slurm_node",
    "k8s_control_node",
    "k8s_worker_node",
    "login_node",
    "login_compiler_node",
]

# Mapping: INI section -> Ansible dynamic host group name (from prepare.yml)
INI_SECTION_TO_GROUP = {
    "slurm_control_node": "slurm_controllers",
    "slurm_node": "slurm_nodes",
    "k8s_control_node": "k8s_masters",
    "k8s_worker_node": "k8s_workers",
    "login_node": "login_nodes",
    "login_compiler_node": "login_compiler_nodes",
}

# Mapping: INI section -> playbook stage variable
INI_SECTION_TO_STAGE = {
    "slurm_control_node": "slurm_ctl",
    "slurm_node": "slurm_node",
    "k8s_control_node": "k8s_master",
    "k8s_worker_node": "k8s_worker",
    "login_node": "login_node",
    "login_compiler_node": "login_compiler_node",
}

# Dynamic host naming pattern (from prepare.yml add_host)
# e.g., k8s_master_10_45_2_105 for IP 10.45.2.105
DYNAMIC_HOST_PATTERNS = {
    "k8s_control_node": "k8s_master_{ip_underscored}",
    "k8s_worker_node": "k8s_worker_{ip_underscored}",
    "slurm_control_node": "slurm_ctl_{ip_underscored}",
    "slurm_node": "slurm_node_{ip_underscored}",
    "login_node": "login_{ip_underscored}",
    "login_compiler_node": "login_compiler_{ip_underscored}",
}

# =============================================================================
# COMMAND CONFIGURATION
# =============================================================================

# The playbook is run directly on the OIM server (not inside a container).
# The ansible.cfg at src/utils/ sets roles_path=roles, so the playbook
# finds the log_collector role automatically.

# Default mode (full/complete logs collection)
LOG_COLLECTION_COMMAND = (
    "cd /omnia/src/utils && ansible-playbook playbooks/collect.yml"
)

# Curated support mode (exclude temporary/stale-old logs via tag)
LOG_COLLECTION_CURATED_MODE = (
    "cd /omnia/src/utils && ansible-playbook playbooks/collect.yml"
    " --tags curated_support"
)

# Playbook path on the OIM server
COLLECT_PLAYBOOK_PATH = "/omnia/src/utils/playbooks/collect.yml"

# =============================================================================
# OUTPUT PATHS (from roles/log_collector/vars/main.yml)
# =============================================================================

# Log collection workspace root on OIM
LOG_ROOT = "/opt/omnia/utils/output/project_default/collect"

OUTPUT_PATHS = {
    "default_output_root": LOG_ROOT,
    "workspace_prefix": "omnia_logs_",
    "bundle_extension": ".tar.gz",
    "metadata_filename": "metadata.json",
    "bundle_dir_pattern": "omnia_logs_*",
    # Subdirectories created during collection (from prepare.yml)
    "k8s_subdir": "k8s",
    "slurm_subdir": "slurm",
}

# =============================================================================
# BUNDLE NAMING PATTERN
# =============================================================================

BUNDLE_NAME_PATTERN = r"omnia_logs_(?P<timestamp>\d{8}-\d{6})\.tar\.gz"
BUNDLE_NAME_FORMAT = "omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz"

# =============================================================================
# LOG PATHS PER FUNCTIONAL GROUP (from roles/log_collector/vars/main.yml)
# =============================================================================

LOG_PATHS: Dict[str, Dict[str, List[str]]] = {
    "k8s_master": {
        "dirs": [
            "/var/log/containers/",
            "/var/log/pods/",
            "/var/log/calico/",
            "/var/log/crio/",
            "/var/log/chrony/",
            "/var/log/private/",
            "/var/log/rhsm/",
        ],
        "files": [
            "/var/log/cloud-init.log",
            "/var/log/cloud-init-output.log",
            "/var/log/dnf.log",
            "/var/log/dnf.rpm.log",
            "/var/log/dnf.librepo.log",
            "/var/log/hawkey.log",
            "/var/log/secure",
            "/var/log/spooler",
        ],
    },
    "k8s_worker": {
        "dirs": [],
        "files": [
            "/var/log/cloud-init.log",
            "/var/log/cloud-init-output.log",
            "/var/log/spooler",
            "/var/log/messages",
            "/var/log/cron",
            "/var/log/secure",
            "/var/log/maillog",
            "/var/log/lastlog",
            "/var/log/btmp",
        ],
    },
    "slurm_ctl": {
        "dirs": [
            "/var/log/slurm/",
            "/var/log/rhsm/",
            "/var/log/private/",
            "/var/log/chrony/",
            "/var/log/munge/",
            "/var/log/insights-client/",
            "/var/log/mariadb/",
        ],
        "files": [
            "/var/log/cloud-init.log",
            "/var/log/cloud-init-output.log",
            "/var/log/ldms-cloudinit.log",
        ],
    },
    "slurm_node": {
        "dirs": [
            "/var/log/slurm/",
        ],
        "files": [
            "/var/log/cloud-init.log",
            "/var/log/cloud-init-output.log",
        ],
    },
    "login_node": {
        "dirs": [
            "/var/log/slurm/",
            "/var/log/chrony/",
            "/var/log/private/",
        ],
        "files": [
            "/var/log/cloud-init.log",
            "/var/log/cloud-init-output.log",
            "/var/log/secure",
            "/var/log/messages",
        ],
    },
    "login_compiler_node": {
        "dirs": [
            "/var/log/slurm/",
            "/var/log/chrony/",
            "/var/log/private/",
        ],
        "files": [
            "/var/log/cloud-init.log",
            "/var/log/cloud-init-output.log",
            "/var/log/secure",
            "/var/log/messages",
        ],
    },
}

# Stage -> output subdirectory (k8s stages go to k8s/, slurm stages go to slurm/)
STAGE_TO_SUBDIR = {
    "k8s_master": "k8s",
    "k8s_worker": "k8s",
    "slurm_ctl": "slurm",
    "slurm_node": "slurm",
    "login_node": "slurm",
    "login_compiler_node": "slurm",
}

# =============================================================================
# METADATA FIELDS (from roles/log_collector/templates/metadata.json.j2)
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

# Warning Entry Schema (from rescue blocks and bundle.yml warning builders)
WARNING_ENTRY_FIELDS = [
    "source",
    "node_name",
    "node_ip",
    "reason",
    "message",
    "timestamp",
]

# Valid warning reasons (from the role's rescue blocks and bundle.yml)
WARNING_REASONS = [
    "unreachable",
    "missing_source",
    "collection_error",
]

# Valid warning sources (stage names used in warning payloads)
WARNING_SOURCES = [
    "k8s_master",
    "k8s_worker",
    "slurm_controller",
    "slurm_node",
    "login_node",
    "login_compiler_node",
]

# =============================================================================
# COLLECTION MODES (aligned with bundle.yml logic)
# =============================================================================

COLLECTION_MODES = {
    "complete logs": {
        "description": "Include all available logs (default mode)",
        "excludes_temp": False,
        "excludes_stale": False,
        "tag": None,
    },
    "curated_support": {
        "description": "Exclude temporary files and stale/old logs",
        "excludes_temp": True,
        "excludes_stale": True,
        "tag": "curated_support",
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
    "ssh_connect": 60,       # Matches ansible.cfg ConnectTimeout
    "command_execution": 300,
    "ansible_timeout": 180,  # Matches ansible.cfg timeout
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
# WARNING PATTERNS (from actual playbook output)
# =============================================================================

WARNING_PATTERNS = {
    "unreachable_node": (
        r"Node\s+(\S+)\s+\(([0-9.]+)\)\s+(?:not reachable|unreachable)"
    ),
    "missing_source": (
        r"Expected log (?:directory|file)\s+(\S+)\s+missing on node\s+(\S+)"
    ),
    "output_not_writable": r"Output directory not writable:\s+(\S+)",
    "archive_failure": r"Bundle archive was not created correctly",
    "disk_full": r"No space left on device",
    "ssh_failed": r"Failed to connect to the host via ssh",
    "collection_error": r"Collection task failed for stage\s+(\S+)",
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
    "input/collect.ini",
]

REQUIRED_SRC_FILES = [
    "input/collect.ini",
]

# =============================================================================
# CENTRALIZED SHELL COMMANDS
# =============================================================================
# All shell commands used by verification functions.
# Use .format() with named placeholders to fill in runtime values.
#
# NOTE: collect.yml runs directly on the OIM host (not inside a container).
# Commands that inspect output artifacts also run on the OIM host directly.

CMDS: Dict[str, str] = {
    # --- Collection ---
    "collect_logs": (
        "cd /omnia/src/utils && ansible-playbook playbooks/collect.yml"
    ),
    "collect_logs_curated": (
        "cd /omnia/src/utils && ansible-playbook playbooks/collect.yml"
        " --tags curated_support"
    ),

    # --- Inventory ---
    "cat_collect_ini": "cat {ini_path}",
    "validate_ini_parse": (
        "python3 -c \""
        "import configparser, json; "
        "c = configparser.ConfigParser(allow_no_value=True); "
        "c.read('{ini_path}'); "
        "print(json.dumps({{s: [k.strip() for k in c[s].keys() "
        "if k.strip() and not k.strip().startswith('#')] "
        "for s in c.sections()}}))\""
    ),

    # --- Workspace / Bundle ---
    "find_workspace": (
        "ls -td {output_root}/{dir_pattern} 2>/dev/null | head -1"
    ),
    "find_bundle": (
        "ls -t {output_root}/omnia_logs_*/*.tar.gz 2>/dev/null | head -1"
    ),
    "dir_exists": "test -d {path} && echo 'exists' || echo 'not_exists'",
    "file_exists": "test -f {path} && echo 'exists' || echo 'not_exists'",

    # --- Metadata ---
    "read_metadata": "cat {workspace}/metadata.json",
    "validate_json": (
        "python3 -c \"import json; json.load(open('{file_path}'))\""
    ),

    # --- Archive ---
    "list_archive": "tar -tzf {archive_path}",
    "extract_archive": "tar -xzf {archive_path} -C {extract_dir}",

    # --- SHA256 ---
    "compute_sha256": "sha256sum {file_path} | awk '{{print $1}}'",

    # --- Permissions / Disk ---
    "set_permissions": "chmod {mode} {path}",
    "check_writable": (
        "test -w {path} && echo 'writable' || echo 'not_writable'"
    ),
    "fill_disk": (
        "dd if=/dev/zero of={path}/fillfile bs=1M count={size_mb} "
        "2>/dev/null || true"
    ),
    "free_disk": "rm -f {path}/fillfile",

    # --- Test file management ---
    "create_temp_file": "touch {path}",
    "create_stale_file": "touch -d '{days} days ago' {path}",
    "remove_file": "rm -f {path}",

    # --- Cleanup ---
    "rm_dir": "rm -rf {path}",
    "rm_file": "rm -f {path}",

    # --- Content checksum ---
    "content_checksum": (
        "find {dir_path} -type f ! -name 'metadata.json' "
        "-exec md5sum {{}} \\; | sort | md5sum"
    ),

    # --- System ---
    "echo_test": "echo connectivity_ok 2>/dev/null",
    "cat_file": "cat {path} 2>/dev/null",

    # --- SSH failure marker ---
    "find_failure_markers": (
        "find {output_root} -name 'SSH_COLLECTION_FAILED.txt' "
        "-type f 2>/dev/null"
    ),
    "read_failure_marker": "cat {marker_path}",
}
