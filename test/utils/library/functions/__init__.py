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
Utils — Functions

All verification, collection, and helper functions.
"""

from .log_collector_func import (
    # Collect.ini / Inventory
    parse_collect_ini,
    verify_collect_ini_exists,
    verify_collect_ini_sections,
    verify_collect_ini_has_nodes,
    get_populated_groups,
    # Collection Execution
    execute_log_collection,
    verify_collection_started,
    verify_inventory_parsed,
    verify_dynamic_hosts_added,
    check_target_connectivity,
    # Workspace
    get_workspace_directory,
    verify_workspace_created,
    verify_workspace_subdirs,
    # Bundle
    get_bundle_path,
    verify_bundle_created,
    verify_bundle_name_format,
    extract_bundle,
    list_bundle_contents,
    verify_bundle_contains_subdirs,
    verify_bundle_contains_node_logs,
    # Metadata
    read_metadata,
    verify_metadata_exists,
    verify_metadata_valid_json,
    verify_metadata_required_fields,
    verify_metadata_collection_mode,
    verify_metadata_warning_entries,
    verify_warning_message_format,
    # Hash
    compute_sha256,
    verify_hash_format,
    verify_hash_in_output,
    verify_hash_match,
    # Output Verification
    verify_completion_summary,
    verify_path_is_absolute,
    verify_warning_summary_in_output,
    # Error / Warning
    set_directory_permissions,
    verify_not_writable_error,
    verify_archive_failure_error,
    verify_unreachable_node_warning,
    verify_missing_source_warning,
    find_ssh_failure_markers,
    # Test File Management
    create_temp_test_files,
    create_stale_test_file,
    cleanup_test_files,
    fill_disk_space,
    free_disk_space,
    # Idempotency
    get_bundle_content_checksum,
    compare_bundle_contents,
    # Cleanup
    cleanup_workspace,
    cleanup_bundle,
)

from .host_func import (
    run_domain_init,
    sync_project_to_remote,
    sync_utils_input,
)

from .validation_func import (
    validate_test_config,
    validate_all,
    ConfigValidationError,
)
