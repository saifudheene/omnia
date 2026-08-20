#!/usr/bin/env python3
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
Dataset Generator — Utils (Log Collector)

Generates custom input datasets for log collector tests.

Usage:
    python generate_dataset.py <name> <profile>
    python generate_dataset.py my_test defaults
"""

import os
import sys
import shutil

import yaml


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.dirname(SCRIPT_DIR)
PROFILES_DIR = os.path.join(SCRIPT_DIR, "profiles")


def load_profile(profile_name: str) -> dict:
    """Load a profile YAML file."""
    profile_path = os.path.join(PROFILES_DIR, f"{profile_name}.yml")
    if not os.path.exists(profile_path):
        print(f"Error: Profile not found: {profile_path}")
        print(f"Available profiles: {list_profiles()}")
        sys.exit(1)

    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_profiles() -> list:
    """List available profile names."""
    if not os.path.exists(PROFILES_DIR):
        return []
    return [
        f.replace(".yml", "")
        for f in os.listdir(PROFILES_DIR)
        if f.endswith(".yml")
    ]


def generate_dataset(name: str, profile: dict):
    """Generate a dataset directory from a profile."""
    dataset_dir = os.path.join(DATASETS_DIR, name)
    input_dir = os.path.join(dataset_dir, "input")

    if os.path.exists(dataset_dir):
        print(f"Warning: Dataset '{name}' already exists at {dataset_dir}")
        response = input("Overwrite? (yes/no): ").strip().lower()
        if response not in ("yes", "y"):
            print("Aborted.")
            sys.exit(0)
        shutil.rmtree(dataset_dir)

    os.makedirs(input_dir, exist_ok=True)

    # Write profile metadata
    meta = {
        "dataset_name": name,
        "profile": profile.get("_profile_name", "unknown"),
        "description": profile.get("description", "Custom dataset"),
    }
    meta_path = os.path.join(dataset_dir, "dataset_meta.yml")
    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, default_flow_style=False)

    print(f"Dataset '{name}' created at {dataset_dir}")
    print(f"  input/          — Place custom input files here")
    print(f"  dataset_meta.yml — Dataset metadata")


def main():
    """Entry point."""
    if len(sys.argv) < 3:
        print("Usage: python generate_dataset.py <name> <profile>")
        print(f"Available profiles: {list_profiles()}")
        sys.exit(1)

    name = sys.argv[1]
    profile_name = sys.argv[2]

    profile = load_profile(profile_name)
    profile["_profile_name"] = profile_name

    generate_dataset(name, profile)


if __name__ == "__main__":
    main()
