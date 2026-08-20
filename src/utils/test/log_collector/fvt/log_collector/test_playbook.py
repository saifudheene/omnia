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
Log Collector — Playbook Deployment Test

Runs collect.yml inside the omnia_core container to produce
a log bundle before the verification tests execute.
"""

import pytest

from library.functions import run_playbook, TestLogger


@pytest.mark.deploy
@pytest.mark.sanity
@pytest.mark.order(0)
def test_deploy_log_collector(host):  # pylint: disable=unused-argument
    """Deploy collect.yml playbook (full mode)."""
    tl = TestLogger("Deploy collect.yml", "TC-F00")
    tl.check("Running collect.yml inside omnia_core container")

    result = run_playbook(timeout=600)

    if result["success"]:
        tl.passed("Playbook completed", result.get("details", ""))
    else:
        tl.failed("Playbook failed", result.get("error", ""))
        pytest.fail(result.get("error", "collect.yml deployment failed"))
