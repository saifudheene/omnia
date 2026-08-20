# Dataset Generator — Utils

Generates custom input datasets for log collector tests.

## Usage

```bash
# Generate a dataset from a profile
python generate_dataset.py <name> <profile>

# Example
python generate_dataset.py my_test defaults
```

## Profiles

Profiles live in `profiles/` and define input overrides:

| Profile | Description |
|---------|-------------|
| `defaults.yml` | Default log collection settings |

## Output

Generated datasets are placed in `datasets/<name>/`:

```
datasets/<name>/
  input/
    # Generated input files
```

## Adding New Profiles

1. Create a YAML file in `profiles/`
2. Define key-value overrides
3. Run the generator with the new profile name
