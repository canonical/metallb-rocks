#
# Copyright 2026 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness.util import docker_util, env_util

# In the future, we may also test ARM
IMG_PLATFORM = "amd64"
IMG_NAME = "frr"

# "ospfd -v" exits immediately after printing the version banner, no
# daemon/socket startup required.
#
# NOTE: bfdd/bgpd do NOT use CRYPTO_OPENSSL on 10.4.1 -- bfd_check_auth()
# in bfdd/bfd_packet.c is an unimplemented stub (always returns false for
# BFD_AUTH_SIMPLE/BFD_AUTH_CRYPTOGRAPHIC, per an upstream TODO comment
# marking that RFC5880 Section 6.7 auth handling is unimplemented).
# --with-crypto=openssl only affects ospfd/ospf6d/ripd/isisd's MD5/SHA
# key-chain auth (ospfd/ospf_auth.c, ripd/ripd.c, ospf6d/ospf6_auth_trailer.c,
# isisd/isis_tlvs.c), which is what this test exercises.


@pytest.mark.parametrize("frr_version", ["10.4.1"])
def test_frr_built_with_openssl_crypto(frr_version: str):
    """FRR must be configured with --with-crypto=openssl so that
    ospfd/ripd/isisd's keyed MD5/SHA authentication links against
    OpenSSL's HMAC/EVP API instead of compiling out the auth path."""
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    docker_run = docker_util.run_in_docker(rock.image, ["/usr/lib/frr/ospfd", "-v"])
    assert "configured with:" in docker_run.stdout
    assert "--with-crypto=openssl" in docker_run.stdout


@pytest.mark.parametrize("frr_version", ["10.4.1"])
def test_frr_links_fips_openssl_module(frr_version: str):
    """The rock must stage the Pro FIPS-validated OpenSSL module so that
    the dynamically-linked libcrypto resolves to it at runtime, not a
    generic libssl3 build with no FIPS provider loaded.

    Note: craft-parts' stage-packages mechanism unpacks .deb file
    contents directly without running dpkg --install, so staged
    packages (openssl-fips-module-3 included) never appear in
    `dpkg -l` -- that would only reflect packages baked into the
    ubuntu@22.04 base image itself. `openssl list -providers` is the
    actual runtime proof: it reports the Pro-signed FIPS provider
    (not just that some file exists on disk).
    """
    rock = env_util.get_build_meta_info_for_rock_version(
        IMG_NAME, frr_version, IMG_PLATFORM
    )

    # ospfd must be dynamically linked against libcrypto for the OpenSSL
    # HMAC/EVP path compiled in by --with-crypto=openssl to be used.
    docker_run = docker_util.run_in_docker(
        rock.image, ["sh", "-c", "ldd /usr/lib/frr/ospfd | grep libcrypto"]
    )
    assert "libcrypto" in docker_run.stdout

    # The Pro FIPS-validated OpenSSL provider must actually load at
    # runtime, not just a generic libssl3 with no FIPS provider configured.
    docker_run = docker_util.run_in_docker(
        rock.image, ["sh", "-c", "openssl list -providers"]
    )
    assert "fips" in docker_run.stdout
    assert "status: active" in docker_run.stdout
