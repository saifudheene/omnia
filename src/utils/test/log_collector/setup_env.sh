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
# log_collector — Environment Setup
# =============================================================================
# Usage:
#   bash setup_env.sh                    # Baremetal or active venv
#   bash setup_env.sh --venv             # Create .venv/ and install there
#   bash setup_env.sh --venv --force     # Recreate .venv/ from scratch
#   bash setup_env.sh --set-password     # Set SSH password for remote mode
#   bash setup_env.sh --password 'pass'  # Non-interactive password
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQ_FILE="${SCRIPT_DIR}/requirements.txt"
CREDS_FILE="${SCRIPT_DIR}/test_creds.yml"
CREDS_KEY="${SCRIPT_DIR}/.test_creds.key"

USE_VENV=false
FORCE_VENV=false
SET_PASSWORD=false
PASSWORD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --venv)          USE_VENV=true; shift ;;
        --force)         FORCE_VENV=true; shift ;;
        --set-password)  SET_PASSWORD=true; shift ;;
        --password)      PASSWORD="$2"; shift 2 ;;
        *)               echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=== Log Collector Test Environment Setup ==="

# --- Virtual environment ---
if [[ "${USE_VENV}" == "true" ]]; then
    if [[ "${FORCE_VENV}" == "true" && -d "${VENV_DIR}" ]]; then
        echo "Removing existing venv..."
        rm -rf "${VENV_DIR}"
    fi

    if [[ ! -d "${VENV_DIR}" ]]; then
        echo "Creating virtual environment at ${VENV_DIR}..."
        python3 -m venv "${VENV_DIR}"
    fi

    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    echo "Activated venv: ${VENV_DIR}"
fi

# --- Install dependencies ---
echo "Installing dependencies from ${REQ_FILE}..."
pip install -q -r "${REQ_FILE}"

# --- Password setup ---
if [[ "${SET_PASSWORD}" == "true" || -n "${PASSWORD}" ]]; then
    # Generate vault key if not exists
    if [[ ! -f "${CREDS_KEY}" ]]; then
        python3 -c "import secrets; print(secrets.token_hex(32))" > "${CREDS_KEY}"
        chmod 600 "${CREDS_KEY}"
        echo "Generated vault key: ${CREDS_KEY}"
    fi

    if [[ -n "${PASSWORD}" ]]; then
        # Non-interactive
        echo "oim_password: \"${PASSWORD}\"" > "${CREDS_FILE}"
    else
        # Interactive
        read -rsp "Enter SSH password: " pw1; echo
        read -rsp "Confirm SSH password: " pw2; echo
        if [[ "${pw1}" != "${pw2}" ]]; then
            echo "ERROR: Passwords do not match"
            exit 1
        fi
        echo "oim_password: \"${pw1}\"" > "${CREDS_FILE}"
    fi

    # Encrypt with ansible-vault
    ansible-vault encrypt "${CREDS_FILE}" --vault-password-file "${CREDS_KEY}"
    echo "Credentials encrypted: ${CREDS_FILE}"
fi

echo ""
echo "=== Setup Complete ==="
echo "Run tests with: ./run_validation.sh log_collector test --marker sanity"
