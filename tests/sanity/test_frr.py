#
# Copyright 2025 Canonical, Ltd.
# See LICENSE file for licensing details
#

import os
import tempfile

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


# Minimal /etc/frr/daemons config mounted into the container to exercise
# the real docker-start entrypoint (frrcommon.sh -> daemon_list() ->
# watchfrr). Regression test for a build-path bug: FRR's ./configure was
# invoked with --prefix/--sbindir pointing at the rockcraft BUILD-stage
# path ($CRAFT_PART_INSTALL/...), which got baked as a literal string
# into the generated frrcommon.sh/watchfrr.sh. At runtime that path
# doesn't exist, so daemon_prep()'s "-x $D_PATH/$daemon" check silently
# failed for every daemon, daemon_list() returned an empty string, and
# docker-start ended up invoking "watchfrr" with zero daemon arguments
# -- which just prints --help and exits 1, never starting any daemon.
MINIMAL_DAEMONS_CONF = """
mgmtd=yes
zebra=yes
bgpd=no
ospfd=no
ospf6d=no
ripd=no
ripngd=no
isisd=no
pimd=no
pim6d=no
ldpd=no
nhrpd=no
eigrpd=no
babeld=no
sharpd=no
pbrd=no
staticd=yes
bfdd=no
fabricd=no
vrrpd=no
vtysh_enable=yes
"""


@pytest.mark.parametrize("frr_version", ["9.0.2", "9.1.0", "9.1.3", "10.4.1", "10.7.1"])
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


@pytest.mark.parametrize("frr_version", ["10.7.1"])
def test_docker_start_boots_daemons(frr_version: str):
    """docker-start must actually start the configured FRR daemons, not
    just print watchfrr's --help text and exit.

    Regression test: FRR's ./configure was invoked with --prefix/
    --sbindir pointing at the rockcraft BUILD-stage path
    ($CRAFT_PART_INSTALL/...), which gets baked as a literal string into
    the generated frrcommon.sh/watchfrr.sh. At runtime that path doesn't
    exist, so every daemon fails frrcommon.sh's daemon_prep() "-x
    $D_PATH/$daemon" check, daemon_list() returns empty, and docker-start
    ends up invoking "watchfrr" with zero daemon arguments -- which just
    prints its own --help text and exits 1, never starting zebra/mgmtd/
    etc. Caught by mounting a minimal /etc/frr/daemons config and
    confirming the entrypoint actually launches daemon processes instead
    of falling back to the help banner.
    """
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as rundir:
        with open(os.path.join(tmpdir, "daemons"), "w") as f:
            f.write(MINIMAL_DAEMONS_CONF)
        open(os.path.join(tmpdir, "frr.conf"), "w").close()
        open(os.path.join(tmpdir, "vtysh.conf"), "w").close()
        os.chmod(tmpdir, 0o777)
        os.chmod(rundir, 0o777)
        for name in ("daemons", "frr.conf", "vtysh.conf"):
            os.chmod(os.path.join(tmpdir, name), 0o666)

        docker_run = docker_util.run_in_docker(
            rock.image,
            ["timeout", "5", "/usr/sbin/docker-start"],
            check_exit_code=False,
            docker_args=[
                "-v",
                f"{tmpdir}:/etc/frr",
                "-v",
                f"{rundir}:/var/run/frr",
            ],
        )

    # The broken path produces "Must specify one or more daemons to
    # monitor." (watchfrr's own argument-count check) and exits 1.
    assert "Must specify one or more daemons to monitor" not in docker_run.stdout
    # "timeout 5" means a successfully-started watchfrr (which runs
    # forever polling daemon status) gets killed with exit 124, not the
    # immediate exit 1 of the broken --help fallback.
    assert docker_run.returncode == 124
