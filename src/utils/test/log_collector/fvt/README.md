# Log Collector — FVT Test Case Registry

Reference: TCASES-LOGEX-2026-001 (v1.0.0)

## Functional Tests (TC-F)

| TC-ID | Name | File | Marker |
|-------|------|------|--------|
| TC-F01 | One-Shot Collection Invocation | `log_collector/collection/test_collection.py` | sanity |
| TC-F02 | Source Collection and Warning Accumulation | `log_collector/collection/test_collection.py` | sanity |
| TC-F03 | Metadata Synthesis and Inclusion | `log_collector/metadata/test_metadata.py` | sanity |
| TC-F04 | Bundle Construction with Deterministic Naming | `log_collector/bundle/test_bundle.py` | sanity |
| TC-F05 | Integrity Hash Generation | `log_collector/bundle/test_bundle.py` | sanity |
| TC-F06 | User-Facing Completion Output | `log_collector/bundle/test_bundle.py` | sanity |

## Negative / Error Tests (TC-E)

| TC-ID | Name | File | Marker | Notes |
|-------|------|------|--------|-------|
| TC-E01 | Output Directory Not Writable | `negative/test_errors.py` | sanity | Skipped (root in container) |
| TC-E02 | Unreachable Node | — | — | Manual only (@lab-only) |
| TC-E03 | Missing Source Files | `negative/test_errors.py` | sanity | |
| TC-E04 | Archive Generation Failure | `negative/test_errors.py` | sanity | |

## Compatibility Tests (TC-C)

| TC-ID | Name | File | Marker |
|-------|------|------|--------|
| TC-C01 | Curated Support Mode | `log_collector/modes/test_modes.py` | sanity |
| TC-C02 | Full Collection Mode | `log_collector/modes/test_modes.py` | sanity |

## Idempotency Tests (TC-I) — NFT

| TC-ID | Name | File | Marker |
|-------|------|------|--------|
| TC-I01 | Collection Command Idempotency | `../nft/test_idempotency.py` | nft |

## Deploy Test

| TC-ID | Name | File | Marker |
|-------|------|------|--------|
| TC-F00 | Deploy collect.yml | `log_collector/test_playbook.py` | deploy, sanity |

## Summary

| Category | Count |
|----------|-------|
| Functional (TC-F) | 6 |
| Negative (TC-E) | 3 (1 skipped, 1 manual) |
| Compatibility (TC-C) | 2 |
| Idempotency (TC-I) | 1 |
| Deploy | 1 |
| **Total** | **13** |
