#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "frr"

V9_0_2_EXPECTED_FILES = [
    "/usr/sbin/docker-start",
    "/usr/lib/frr/watchfrr",
]

# Just a line that the help string is expected to contain.
V9_0_2_EXPECTED_HELPSTR = "Watchdog program to monitor status of frr daemons"


def test_sanity():
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, "9.0.2", IMG_PLATFORM
    )

    # check rock filesystem
    docker_util.ensure_image_contains_paths(rock.image, V9_0_2_EXPECTED_FILES)

    docker_run = docker_util.run_in_docker(rock.image, ["/usr/lib/frr/watchfrr", "--help"])
    assert V9_0_2_EXPECTED_HELPSTR in docker_run.stdout
