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
Utils — Variables

Common constants, paths, container names, and command templates.
"""

from .common_vars import (
    MODULE_ROOT,
    MONOREPO_ROOT,
    SRC_INPUT_DIR,
    DOMAIN_NAME,
    ENV_OMNIA_DATA_PATH,
    ENV_OMNIA_PROJECT_NAME,
    CONTAINER_NAME,
    PLAYBOOK_ENTRY_POINT,
    PLAYBOOK_WORKDIR,
    PLAYBOOK_TAGS,
    PLAYBOOK_STAGES,
    COLLECT_INI_PATH,
    COLLECT_INI_SRC,
    COLLECT_INI_SECTIONS,
    INI_SECTION_TO_GROUP,
    INI_SECTION_TO_STAGE,
    DYNAMIC_HOST_PATTERNS,
    LOG_COLLECTION_COMMAND,
    LOG_COLLECTION_CURATED_MODE,
    COLLECT_PLAYBOOK_PATH,
    LOG_ROOT,
    BUNDLE_NAME_PATTERN,
    BUNDLE_NAME_FORMAT,
    OUTPUT_PATHS,
    LOG_PATHS,
    STAGE_TO_SUBDIR,
    METADATA_REQUIRED_FIELDS,
    WARNING_ENTRY_FIELDS,
    WARNING_REASONS,
    WARNING_SOURCES,
    COLLECTION_MODES,
    TEST_FILES,
    SHA256_CONFIG,
    TIMEOUTS,
    EXIT_CODES,
    WARNING_PATTERNS,
    TEST_CONFIG,
    IPV4_PATTERN,
    REQUIRED_CONFIG_FIELDS,
    REQUIRED_DATASET_FILES,
    REQUIRED_SRC_FILES,
    CMDS,
)

from .test_case_vars import TEST_CASES
