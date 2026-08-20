#!/usr/bin/env bash
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

# =============================================================================
# log_collector — Validation Runner
# =============================================================================
# Usage:
#   ./run_validation.sh <scenario> <command> [options]
#   ./run_validation.sh --config
#   ./run_validation.sh list
#
# Commands:
#   deploy    Run the playbook only (tests marked @deploy)
#   verify    Run verification tests only (exclude @deploy)
#   test      Deploy + Verify (full flow)
#
# FVT Scenarios:
#   log_collector     Full end-to-end (deploy + verify)
#   negative          Error handling tests
#
# NFT Scenarios:
#   nft               Non-functional tests (idempotency)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FVT_DIR="${SCRIPT_DIR}/fvt"
NFT_DIR="${SCRIPT_DIR}/nft"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# FVT scenarios
FVT_SCENARIOS=("log_collector" "negative")
NFT_SCENARIOS=("nft")
ALL_SCENARIOS=("${FVT_SCENARIOS[@]}" "${NFT_SCENARIOS[@]}")

usage() {
    echo -e "${CYAN}Usage:${NC}"
    echo -e "  $0 <scenario> <command> [options]"
    echo -e "  $0 list"
    echo -e "  $0 --help"
    echo ""
    echo -e "${CYAN}Scenarios:${NC}"
    echo -e "  ${GREEN}log_collector${NC}    Full end-to-end (deploy + verify)"
    echo -e "  ${GREEN}negative${NC}         Error handling tests"
    echo -e "  ${GREEN}nft${NC}              Non-functional tests (idempotency)"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo -e "  ${GREEN}deploy${NC}    Run the playbook only"
    echo -e "  ${GREEN}verify${NC}    Run verification tests only"
    echo -e "  ${GREEN}test${NC}      Deploy + Verify (full flow)"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo -e "  --suite <name>    Filter by subfolder (collection, metadata, bundle, modes)"
    echo -e "  --marker <expr>   Filter by marker (sanity, nft)"
    echo -e "  --debug           Full debug output (pytest -vvs)"
    echo -e "  -v, --verbose     Increase verbosity"
}

list_scenarios() {
    echo -e "${CYAN}Available scenarios:${NC}"
    echo ""
    echo -e "  ${BLUE}FVT (Functional Verification):${NC}"
    for s in "${FVT_SCENARIOS[@]}"; do
        echo -e "    ${GREEN}${s}${NC}"
    done
    echo ""
    echo -e "  ${BLUE}NFT (Non-Functional):${NC}"
    for s in "${NFT_SCENARIOS[@]}"; do
        echo -e "    ${GREEN}${s}${NC}"
    done
}

run_pytest() {
    local test_path="$1"
    shift
    local pytest_args=("$@")

    echo -e "${BLUE}Running:${NC} pytest ${test_path} ${pytest_args[*]}"
    python -m pytest "${test_path}" "${pytest_args[@]}" || true
}

# --- Main ---
if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

case "$1" in
    --help|-h)
        usage
        exit 0
        ;;
    list)
        list_scenarios
        exit 0
        ;;
esac

SCENARIO="${1:-}"
COMMAND="${2:-test}"
shift 2 || true

# Parse options
SUITE=""
MARKER=""
VERBOSE=""
DEBUG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --suite)   SUITE="$2"; shift 2 ;;
        --marker)  MARKER="$2"; shift 2 ;;
        --debug)   DEBUG="-vvs"; shift ;;
        -v|--verbose) VERBOSE="-v"; shift ;;
        *)         echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

# Resolve test path
if [[ " ${NFT_SCENARIOS[*]} " =~ " ${SCENARIO} " ]]; then
    TEST_PATH="${NFT_DIR}"
else
    TEST_PATH="${FVT_DIR}/${SCENARIO}"
fi

if [[ -n "${SUITE}" ]]; then
    TEST_PATH="${TEST_PATH}/${SUITE}"
fi

if [[ ! -d "${TEST_PATH}" ]]; then
    echo -e "${RED}Scenario path not found: ${TEST_PATH}${NC}"
    exit 1
fi

# Build pytest args
PYTEST_ARGS=()
[[ -n "${DEBUG}" ]] && PYTEST_ARGS+=("${DEBUG}")
[[ -n "${VERBOSE}" ]] && PYTEST_ARGS+=("${VERBOSE}")
[[ -n "${MARKER}" ]] && PYTEST_ARGS+=("--marker" "${MARKER}")

# Execute
cd "${SCRIPT_DIR}"

case "${COMMAND}" in
    deploy)
        echo -e "${CYAN}=== Deploy: ${SCENARIO} ===${NC}"
        PYTEST_ARGS+=("-m" "deploy")
        run_pytest "${TEST_PATH}" "${PYTEST_ARGS[@]}"
        ;;
    verify)
        echo -e "${CYAN}=== Verify: ${SCENARIO} ===${NC}"
        PYTEST_ARGS+=("-m" "not deploy")
        run_pytest "${TEST_PATH}" "${PYTEST_ARGS[@]}"
        ;;
    test)
        echo -e "${CYAN}=== Test (Deploy + Verify): ${SCENARIO} ===${NC}"
        run_pytest "${TEST_PATH}" "${PYTEST_ARGS[@]}"
        ;;
    *)
        echo -e "${RED}Unknown command: ${COMMAND}${NC}"
        usage
        exit 1
        ;;
esac
