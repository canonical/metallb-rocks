#
# Copyright 2025 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "frr"

EXPECTED_FILES = [
    "/usr/sbin/docker-start",
    "/usr/lib/frr/watchfrr",
]

# Just a line that the help string is expected to contain.
EXPECTED_HELPSTR = "Watchdog program to monitor status of frr daemons"


@pytest.mark.parametrize("frr_version", ["9.0.2", "9.1.0", "9.1.3"])
def test_sanity(frr_version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    # check rock filesystem
    docker_util.ensure_image_contains_paths(rock.image, EXPECTED_FILES)

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/lib/frr/watchfrr", "--help"]
    )
    assert EXPECTED_HELPSTR in docker_run.stdout
