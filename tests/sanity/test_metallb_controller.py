#
# Copyright 2025 Canonical, Ltd.
# See LICENSE file for licensing details
#

from typing import List

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "metallb-controller"

V0_14_5_EXPECTED_FILES = [
    "/controller",
    "LICENSE",
]

# Just a line that the help string is expected to contain.
EXPECTED_HELPSTR = "Usage of /controller:"


@pytest.mark.parametrize(
    "metallb_version,expected_files",
    [
        ("v0.14.5", V0_14_5_EXPECTED_FILES),
        ("v0.14.8", V0_14_5_EXPECTED_FILES),
        ("v0.14.9", V0_14_5_EXPECTED_FILES),
    ],
)
def test_sanity(metallb_version: str, expected_files: List[str]):
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, metallb_version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/controller", "--help"])
    assert EXPECTED_HELPSTR in docker_run.stderr

    # check rock filesystem
    docker_util.ensure_image_contains_paths_bare(rock.image, expected_files)
