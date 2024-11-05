#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "metallb-speaker"

V0_14_5_EXPECTED_FILES = [
    "/speaker",
    "LICENSE",
]

# Just a line that the help string is expected to contain.
V0_14_5_EXPECTED_HELPSTR = "Usage of /speaker:"


def test_sanity():
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, "v0.14.5", IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/speaker", "--help"])
    assert V0_14_5_EXPECTED_HELPSTR in docker_run.stderr

    # check rock filesystem
    docker_util.ensure_image_contains_paths_bare(rock.image, V0_14_5_EXPECTED_FILES)
