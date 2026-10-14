#
# Copyright 2026 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "frr-k8s"

EXPECTED_FILES = [
    "/frr-k8s",
    "/statuscleaner",
    "/frr-metrics",
    "/frr-status",
    "/frr-reloader.sh",
    "/LICENSE",
    # Required by the chart's init containers.
    "/bin/sh",
    "/bin/cp",
]

# Just a line that the help string is expected to contain.
EXPECTED_HELPSTR = "Usage of /frr-k8s:"


@pytest.mark.parametrize("frr_k8s_version", ["v0.0.25"])
def test_sanity(frr_k8s_version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_k8s_version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/frr-k8s", "--help"])
    assert EXPECTED_HELPSTR in docker_run.stderr

    # check rock filesystem
    docker_util.ensure_image_contains_paths_bare(rock.image, EXPECTED_FILES)
