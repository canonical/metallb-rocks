#
# Copyright 2025 Canonical, Ltd.
# See LICENSE file for licensing details
#

from typing import List

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "frr"

V9_0_2_EXPECTED_FILES = [
    "/usr/sbin/docker-start",
    "/usr/lib/frr/watchfrr",
]

# Paths the frr-k8s chart relies on in the FRR image.
V10_4_3_EXPECTED_FILES = [
    "/sbin/tini",
    "/usr/lib/frr/docker-start",
    "/usr/lib/frr/watchfrr",
    "/usr/lib/frr/frr-reload.py",
    "/usr/bin/vtysh",
    "/usr/bin/python3",
]

# Just a line that the help string is expected to contain.
EXPECTED_HELPSTR = "Watchdog program to monitor status of frr daemons"

# Capabilities the frr-k8s chart grants to the FRR container.
FRR_CAPS = ["NET_ADMIN", "NET_RAW", "SYS_ADMIN"]

# Starts FRR the way the frr-k8s chart does, with bgpd enabled, then applies
# a BGP config through frr-reload.py as the frr-k8s reloader does. Prints the
# running daemons and the resulting running config.
START_FRR_SCRIPT = """
mkdir -p /var/run/frr && chown frr:frr /var/run/frr
sed -i 's/^bgpd=no/bgpd=yes/' /etc/frr/daemons
/sbin/tini -- /usr/lib/frr/docker-start &
for _ in $(seq 30); do
    vtysh -c 'show daemons' 2>/dev/null | grep -q bgpd && break
    sleep 1
done
vtysh -c 'show daemons'

printf 'router bgp 64512\\n bgp router-id 10.0.0.1\\nexit\\n' > /etc/frr/frr.conf.new
python3 /usr/lib/frr/frr-reload.py --reload --overwrite --stdout /etc/frr/frr.conf.new
vtysh -c 'show running-config'
"""

EXPECTED_OUTPUT = ["zebra", "bgpd", "staticd", "watchfrr", "router bgp 64512"]


@pytest.mark.parametrize(
    "frr_version,expected_files",
    [
        ("9.0.2", V9_0_2_EXPECTED_FILES),
        ("9.1.0", V9_0_2_EXPECTED_FILES),
        ("9.1.3", V9_0_2_EXPECTED_FILES),
        ("10.4.1", V9_0_2_EXPECTED_FILES),
        ("10.4.3", V10_4_3_EXPECTED_FILES),
    ],
)
def test_sanity(frr_version: str, expected_files: List[str]):
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    # check rock filesystem
    docker_util.ensure_image_contains_paths(rock.image, expected_files)

    docker_run = docker_util.run_in_docker(
        rock.image, ["/usr/lib/frr/watchfrr", "--help"]
    )
    assert EXPECTED_HELPSTR in docker_run.stdout


@pytest.mark.parametrize("frr_version", ["10.4.3"])
def test_frr_starts(frr_version: str):
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    docker_args = [f"--cap-add={cap}" for cap in FRR_CAPS]
    docker_run = docker_util.run_in_docker(
        rock.image, ["/bin/bash", "-c", START_FRR_SCRIPT], docker_args=docker_args
    )

    for expected in EXPECTED_OUTPUT:
        assert expected in docker_run.stdout
