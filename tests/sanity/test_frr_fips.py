#
# Copyright 2026 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "frr"

# Daemons link bfdd/bgpd's HMAC-SHA1 path to OpenSSL. "bfdd -v" exits
# immediately after printing the version banner, no daemon/socket
# startup required.


@pytest.mark.parametrize("frr_version", ["10.7.1"])
def test_frr_built_with_openssl_crypto(frr_version: str):
    """FRR must be configured with --with-crypto=openssl so that bfdd's
    keyed-SHA1 BFD authentication (bfdd/bfd_packet.c) links against
    OpenSSL's HMAC/EVP API instead of compiling out the auth path."""
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/usr/lib/frr/bfdd", "-v"])
    assert "configured with:" in docker_run.stdout
    assert "--with-crypto=openssl" in docker_run.stdout


@pytest.mark.parametrize("frr_version", ["10.7.1"])
def test_frr_links_fips_openssl_module(frr_version: str):
    """The rock must stage the Pro FIPS-validated OpenSSL module so that
    the dynamically-linked libcrypto resolves to it at runtime, not a
    generic libssl3 build with no FIPS provider loaded.

    Note: craft-parts' stage-packages mechanism unpacks .deb file
    contents directly without running dpkg --install, so staged
    packages (openssl-fips-module-3 included) never appear in
    `dpkg -l` -- that would only reflect packages baked into the
    ubuntu@22.04 base image itself.

    Note: `openssl list -providers` only reports the `fips` provider
    as active when the *host* kernel has FIPS mode enabled
    (/proc/sys/crypto/fips_enabled=1) -- on this CI runner (plain
    ubuntu-22.04, not Pro/FIPS-attached), the same correctly-built
    image reports only the `default` provider even though the FIPS
    module is staged. Checking for that would make this test fail on
    every CI run regardless of whether the rock is correct.
    `openssl fipsinstall -module ... -out ...` is host-independent: it
    loads the module and runs its own cryptographic self-tests,
    succeeding only if the module file is present, uncorrupted, and
    passes self-test -- proof the module was actually staged.
    """
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    # bfdd (and bgpd) must be dynamically linked against libcrypto for the
    # OpenSSL HMAC/EVP path compiled in by --with-crypto=openssl to be used.
    docker_run = docker_util.run_in_docker(
        rock.image, ["sh", "-c", "ldd /usr/lib/frr/bfdd | grep libcrypto"]
    )
    assert "libcrypto" in docker_run.stdout

    # The Pro FIPS-validated OpenSSL module must be present and pass its
    # own self-test, independent of the host kernel's FIPS mode.
    docker_run = docker_util.run_in_docker(
        rock.image,
        [
            "sh",
            "-c",
            "openssl fipsinstall "
            "-module /usr/lib/x86_64-linux-gnu/ossl-modules-3/fips.so "
            "-out /tmp/fipsmodule.cnf -quiet && cat /tmp/fipsmodule.cnf",
        ],
    )
    assert "activate = 1" in docker_run.stdout
