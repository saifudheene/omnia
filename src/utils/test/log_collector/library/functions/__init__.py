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

Common utilities come from the omnia_auto package.
Module-specific functions remain here.
"""

# --- Common (from omnia_auto package) ---
from omnia_auto import (
    Colors,
    Symbols,
    log,
    TestLogger,
    get_test_output,
    get_testinfra_host,
    load_test_config,
    load_test_credentials,
    get_module_root,
    run_on_host,
    is_local_execution,
    TestReport,
    get_current_report,
    set_current_report,
    run_playbook as _run_playbook,
)
from ..vars.log_collector_vars import PLAYBOOK_ENTRY_POINT, PLAYBOOK_WORKDIR

# --- Log Collector verification ---
from .log_collector_func import (
    execute_log_collection,
    verify_collection_started,
    get_workspace_directory,
    verify_workspace_created,
    get_bundle_path,
    verify_bundle_created,
    verify_bundle_name_format,
    extract_bundle,
    list_bundle_contents,
    verify_bundle_contains_file,
    read_metadata,
    verify_metadata_exists,
    verify_metadata_valid_json,
    verify_metadata_required_fields,
    verify_metadata_warning_entries,
    verify_warning_message_format,
    compute_sha256,
    verify_hash_format,
    verify_hash_in_output,
    verify_hash_match,
    verify_output_contains_path,
    verify_path_is_absolute,
    verify_warning_summary_in_output,
    set_directory_permissions,
    verify_not_writable_error,
    verify_archive_failure_error,
    verify_unreachable_node_warning,
    verify_missing_source_warning,
    create_temp_test_files,
    create_stale_test_file,
    cleanup_test_files,
    fill_disk_space,
    free_disk_space,
    get_bundle_content_checksum,
    compare_bundle_contents,
    cleanup_workspace,
    cleanup_bundle,
)


def run_playbook(tag=None, **kwargs):
    """Wrapper that injects module-specific playbook and workdir."""
    return _run_playbook(
        playbook=kwargs.pop("playbook", PLAYBOOK_ENTRY_POINT),
        playbook_workdir=kwargs.pop("playbook_workdir", PLAYBOOK_WORKDIR),
        tag=tag,
        **kwargs,
    )
