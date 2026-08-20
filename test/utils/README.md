# Utils — Test Automation

Functional Verification Testing (FVT) for the **utils** domain, specifically
the **log collector** (`collect.yml`) playbook.

## Directory Structure

```
test/utils/
├── conftest.py               # Pytest configuration (host fixture, markers, report)
├── run_validation.sh          # Entrypoint: setup + run tests
├── setup_env.sh               # Install dependencies, configure credentials
├── test_config.yml            # Target server IP, sync settings
├── test_creds.yml             # Credentials (auto-encrypted, gitignored)
├── test_run_config.yml        # Suite execution order and marker filters
├── requirements.txt           # Python dependencies
├── .gitignore
├── README.md
│
├── library/                   # Domain-specific test library
│   ├── __init__.py
│   ├── functions/
│   │   ├── __init__.py        # Re-exports from omnia_auto + module functions
│   │   ├── log_collector_func.py  # Log collector verification functions
│   │   ├── host_func.py      # Sync utilities (project, input)
│   │   └── validation_func.py # Config validation
│   ├── vars/
│   │   ├── __init__.py        # Re-exports all vars + TEST_CASES
│   │   ├── common_vars.py    # Module constants, paths, CMDS
│   │   └── test_case_vars.py # TEST_CASES registry (TC IDs + titles)
│   └── messages/
│       ├── __init__.py        # Re-exports TEST_LOG_MSGS, TEST_ASSERT_MSGS
│       └── log_collector_msgs.py  # All user-facing messages
│
├── fvt/                       # Functional Verification Tests
│   ├── log_collector/         # Log collection scenario
│   │   ├── collection/test_collection.py   # TC-F01, TC-F02
│   │   ├── metadata/test_metadata.py       # TC-F03
│   │   ├── bundle/test_bundle.py           # TC-F04, TC-F05, TC-F06
│   │   └── modes/test_modes.py             # TC-C01, TC-C02
│   └── negative/              # Error handling scenario
│       └── test_errors.py                  # TC-E01, TC-E03, TC-E04
│
├── nft/                       # Non-Functional Tests
│   └── test_idempotency.py                 # TC-I01
│
├── datasets/                  # Generated test input data
│   ├── generator/             # Dataset generation tool
│   └── README.md
│
└── ut/                        # Unit tests (future)
```

## Quick Start

```bash
# 1. Set up environment (on OIM server or remote workstation)
cd test/utils/
bash setup_env.sh

# 2. For remote mode, set target IP
vi test_config.yml  # Set oim_server_ip

# 3. Run all tests
bash run_validation.sh

# 4. Run specific suite
pytest fvt/log_collector/ -v

# 5. Run with marker filter
pytest fvt/ --marker sanity -v
```

## Test Cases

| TC ID   | Title                                     | File                          |
|---------|-------------------------------------------|-------------------------------|
| TC-F01  | One-Shot Collection Invocation            | collection/test_collection.py |
| TC-F02  | Source Collection and Warning Accumulation | collection/test_collection.py |
| TC-F03  | Metadata Synthesis and Inclusion          | metadata/test_metadata.py     |
| TC-F04  | Bundle Construction with Deterministic Naming | bundle/test_bundle.py     |
| TC-F05  | Integrity Hash Generation                 | bundle/test_bundle.py         |
| TC-F06  | User-Facing Completion Output             | bundle/test_bundle.py         |
| TC-E01  | Output Directory Not Writable (skipped)   | negative/test_errors.py       |
| TC-E03  | Missing Source Files — Warning Emitted    | negative/test_errors.py       |
| TC-E04  | Archive Generation Failure                | negative/test_errors.py       |
| TC-C01  | Curated Support Mode                      | modes/test_modes.py           |
| TC-C02  | Full Collection Mode                      | modes/test_modes.py           |
| TC-I01  | Collection Command Idempotency            | nft/test_idempotency.py       |

## Reference Specifications

- BSPEC-LOGEX-2026-001 (Behavior Specification)
- CSPEC-LOGEX-2026-001 (Component Specification)
- TCASES-LOGEX-2026-001 (Test Cases)
