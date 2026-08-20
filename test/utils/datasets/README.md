# Datasets

Test input configuration for the `utils` (log collector) automation framework.

## Default Mode (Recommended)

By default (`dataset: ""` in `test_config.yml`), the framework reads input
files **directly from `src/`** — no dataset folder is needed.

The log collector tests primarily verify playbook behavior and do not require
custom input datasets. The default mode is recommended for most use cases.

## Custom Datasets

Set `dataset: "my_ds"` in `test_config.yml` to use a custom dataset
from `datasets/<name>/`. Generate one with the dataset generator:

```bash
cd datasets/generator/
python generate_dataset.py my_ds defaults
```

See [`generator/README.md`](generator/README.md) for full usage.

### Custom Dataset Structure

```
datasets/<name>/
  input/
    # Custom input files for log collection (if applicable)
```

## Switching Datasets

### Edit `test_config.yml`
```yaml
dataset: "my_custom_ds"    # Use custom dataset
dataset: ""                # Use src/ (default)
```

### Per-scenario override in `test_run_config.yml`
```yaml
scenarios:
  log_collector:
    dataset: "my_custom_ds"
```

### Environment variable (one-off)
```bash
OMNIA_DATASET_OVERRIDE=my_custom_ds ./run_validation.sh log_collector verify
```

**Priority**: env var > per-scenario override > `test_config.yml` default.
