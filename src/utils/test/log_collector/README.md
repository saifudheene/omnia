# Log Collector (collect.yml) — Test Automation

Functional Verification Testing (FVT) for the `log_collector` role
(playbook: `collect.yml`) inside the **omnia.utils** Ansible Galaxy collection.

Validates one-shot combined log extraction from Kubernetes and Slurm cluster
nodes, including collection invocation, metadata synthesis, bundle construction,
SHA256 integrity verification, error handling, and idempotency.

Uses the **`omnia-auto`** package (from `test/plugins/`) for common test
utilities (host connection, playbook runner, report generation, formatting).

---

## Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| Python | 3.12+ | `python3 --version` |
| `sshpass` | — | `yum install sshpass` (only if password-based SSH) |
| Ansible | 2.15+ | Installed automatically by `setup_env.sh` |

### Target Server Setup

The target OIM server must have:
- `omnia_core` container running (`omnia.sh --install` completed)
- Service K8s cluster deployed (for K8s log collection)
- Slurm cluster deployed (optional, for Slurm log collection)

---

## Setup

```bash
# Step 1 — Enter the test directory
cd omnia/src/utils/test/log_collector/

# Step 2 — Configure the target server
vi test_config.yml       # Set oim_server_ip for remote mode

# Step 3 — Run setup
bash setup_env.sh                    # Baremetal or active venv
bash setup_env.sh --venv             # Create .venv/ and install there

# Step 4 — Set SSH password (required for remote mode)
bash setup_env.sh --set-password     # Interactive prompt

# Step 5 — Activate environment (if using --venv mode)
source .venv/bin/activate

# Step 6 — Run tests
./run_validation.sh log_collector test --marker sanity
```

---

## Running Tests

```
./run_validation.sh <scenario> <command> [options]
./run_validation.sh list              # List available scenarios
./run_validation.sh --help            # Full usage
```

### Commands

| Command | Description |
|---------|-------------|
| `deploy` | Run the Ansible playbook only |
| `verify` | Run verification tests only (no playbook) |
| `test` | Full flow: deploy + verify |

### FVT Scenarios

| Scenario | What It Tests |
|----------|---------------|
| `log_collector` | Full end-to-end: invoke collect.yml, verify workspace, bundle, metadata, hash, output |
| `negative` | Error handling: missing sources, archive failure, output not writable |

### NFT Scenario

| Scenario | What It Tests |
|----------|---------------|
| `nft` | Idempotency: two consecutive runs produce deterministic results |

### Options

| Option | Description |
|--------|-------------|
| `--suite <name>` | Filter by subfolder (`collection`, `metadata`, `bundle`, `modes`) |
| `--marker <expr>` | Filter by marker (`sanity`, `nft`) |
| `--debug` | Full debug output (pytest -vvs) |
| `-v, --verbose` | Increase pytest verbosity |

### Typical Workflow

```bash
./run_validation.sh log_collector test --marker sanity    # 1. Full FVT
./run_validation.sh log_collector verify --suite metadata  # 2. Metadata only
./run_validation.sh negative verify                        # 3. Error handling
./run_validation.sh nft test                               # 4. Idempotency
```

---

## Test Cases

| TC-ID | Name | Type | Scenario |
|-------|------|------|----------|
| TC-F01 | One-Shot Collection Invocation | Functional | log_collector |
| TC-F02 | Source Collection and Warning Accumulation | Functional | log_collector |
| TC-F03 | Metadata Synthesis and Inclusion | Functional | log_collector |
| TC-F04 | Bundle Construction with Deterministic Naming | Functional | log_collector |
| TC-F05 | Integrity Hash Generation | Functional | log_collector |
| TC-F06 | User-Facing Completion Output | Functional | log_collector |
| TC-E01 | Output Directory Not Writable | Negative | negative (skipped) |
| TC-E03 | Missing Source Files - Warning Emitted | Negative | negative |
| TC-E04 | Archive Generation Failure | Negative | negative |
| TC-I01 | Collection Command Idempotency | NFT | nft |
| TC-C01 | Curated Support Mode | Compatibility | log_collector |
| TC-C02 | Full Collection Mode | Compatibility | log_collector |

**Total: 12 test cases** (11 active + 1 skipped)

Note: TC-E02 (Unreachable Node) is manual only (@lab-only).

---

## Directory Structure

```
src/utils/test/log_collector/
├── setup_env.sh                 # Environment setup
├── run_validation.sh            # CLI runner
├── conftest.py                  # Pytest hooks, fixtures, report generation
├── test_config.yml              # Target server and settings
├── test_creds.yml               # SSH credentials (Ansible Vault, gitignored)
├── .test_creds.key              # Vault encryption key (gitignored)
├── test_run_config.yml          # Batch execution config
├── requirements.txt             # Python dependencies
├── .gitignore
├── README.md
│
├── library/                     # Reusable automation library
│   ├── __init__.py
│   ├── functions/
│   │   ├── __init__.py          # omnia_auto imports + run_playbook wrapper
│   │   └── log_collector_func.py  # 30+ verification functions
│   ├── vars/
│   │   ├── __init__.py          # TEST_CASES registry
│   │   └── log_collector_vars.py  # Constants, paths, commands
│   └── messages/
│       ├── __init__.py
│       └── log_collector_msgs.py  # Test names, log/assert messages
│
├── fvt/                         # Functional Verification Tests
│   ├── log_collector/           # Primary scenario
│   │   ├── test_playbook.py     # Deploy collect.yml
│   │   ├── collection/
│   │   │   └── test_collection.py   # TC-F01, TC-F02
│   │   ├── metadata/
│   │   │   └── test_metadata.py     # TC-F03
│   │   ├── bundle/
│   │   │   └── test_bundle.py       # TC-F04, TC-F05, TC-F06
│   │   └── modes/
│   │       └── test_modes.py        # TC-C01, TC-C02
│   └── negative/
│       └── test_errors.py           # TC-E01, TC-E03, TC-E04
│
└── nft/                         # Non-Functional Tests
    └── test_idempotency.py          # TC-I01
```

---

## Migration from Automation_Repo (omnia-containers)

This module was migrated from the Molecule-based `one_shot_log_extraction`
scenario in the `omnia-containers` automation repo:

| Area | Old (omnia-containers) | New (omnia monorepo) |
|------|------------------------|----------------------|
| **Runner** | `molecule test -s one_shot_log_extraction` | `./run_validation.sh log_collector test` |
| **Framework** | Molecule + testinfra | `run_validation.sh` + pytest + `omnia-auto` |
| **Library** | `automation_library/one_shot_log_extraction/` | `src/utils/test/log_collector/library/` |
| **Tests** | `molecule/.../tests/sanity/test_one_shot_log_extraction.py` | `fvt/log_collector/` (split by concern) |
| **Host conn** | `automation_library.core.get_node_admin_ip` | `omnia_auto.get_testinfra_host` |
| **Cmd exec** | `automation_library.core.run_on_remote_node` | `omnia_auto.run_on_host` |
| **Config** | `omnia_test_config.yml` + PXE mapping | `test_config.yml` + `omnia.env` on target |
| **Credentials** | `omnia_test_credentials.yml` | `test_creds.yml` (Ansible Vault) |
| **Playbook path** | `/omnia/log_collector/collect.yml` | `/omnia/src/utils/playbooks/collect.yml` |

### Key Changes

1. **Import paths**: `from ...core import run_on_remote_node` replaced with
   `from omnia_auto import run_on_host`
2. **Playbook path**: Updated from `/omnia/log_collector/` to
   `/omnia/src/utils/playbooks/` (domain-segregated structure)
3. **Test splitting**: Single 959-line test file split into 6 focused files
   organized by concern (collection, metadata, bundle, modes, errors, idempotency)
4. **No Molecule dependency**: Direct pytest execution via `run_validation.sh`

---

## Using the `omnia-auto` Pip Package

| Category | Functions used |
|----------|---------------|
| **Config** | `configure()`, `load_test_config()`, `load_test_credentials()` |
| **Host** | `get_testinfra_host()`, `is_local_execution()`, `run_on_host()` |
| **Runner** | `run_playbook()` — wrapped with module-specific playbook/workdir |
| **Formatting** | `TestLogger`, `Colors`, `Symbols`, `log()`, `add_session_result()` |
| **Report** | `TestReport`, `set_current_report()`, `get_current_report()` |
