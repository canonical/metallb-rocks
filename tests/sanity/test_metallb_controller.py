#
# Copyright 2025 Canonical, Ltd.
# See LICENSE file for licensing details
#

import shlex
from pathlib import Path
from typing import List

import pytest
from k8s_test_harness.util import docker_util, env_util, fips_util

# In the future, we may also test ARM
TEST_PATH = Path(__file__)
REPO_PATH = TEST_PATH.parent.parent.parent
IMAGE_NAME = "metallb-controller"
IMAGE_BASE = f"ghcr.io/canonical/{IMAGE_NAME}"
IMAGE_ENTRYPOINT = "/controller --help"
PEBBLE_VERSION = "v1.18.0"

V0_14_5_EXPECTED_FILES = [
    "/controller",
    "LICENSE",
]

# Just a line that the help string is expected to contain.
EXPECTED_HELPSTR = "Usage of /controller:"


@pytest.mark.parametrize(
    "version,expected_files",
    [
        ("v0.14.5", V0_14_5_EXPECTED_FILES),
        ("v0.14.8", V0_14_5_EXPECTED_FILES),
        ("v0.14.9", V0_14_5_EXPECTED_FILES),
    ],
)
def test_filesystem(image_version: str, expected_files: List[str]):
    image = env_util.get_build_meta_info_for_rock_version(IMAGE_NAME, image_version, "amd64")
    docker_util.ensure_image_contains_paths_bare(image, expected_files)


@pytest.mark.parametrize(
    "image_version", env_util.image_versions_in_repo(IMAGE_NAME, REPO_PATH)
)
def test_executable(image_version):
    image = env_util.get_build_meta_info_for_rock_version(IMAGE_NAME, image_version, "amd64")
    docker_util.run_entrypoint_and_assert(
        image, IMAGE_ENTRYPOINT, expect_stderr_contains=EXPECTED_HELPSTR
    )


@pytest.mark.parametrize(
    "image_version", env_util.image_versions_in_repo(IMAGE_NAME, REPO_PATH)
)
def test_pebble_executable(image_version):
    image = env_util.get_build_meta_info_for_rock_version(IMAGE_NAME, image_version, "amd64")
    docker_util.run_entrypoint_and_assert(
        image, "/bin/pebble version", expect_stdout_contains=PEBBLE_VERSION
    )


@pytest.mark.parametrize("GOFIPS", [0, 1], ids=lambda v: f"GOFIPS={v}")
@pytest.mark.parametrize(
    "image_version", env_util.image_versions_in_repo(IMAGE_NAME, REPO_PATH)
)
def test_fips(image_version, GOFIPS):
    image = env_util.get_build_meta_info_for_rock_version(IMAGE_NAME, image_version, "amd64")
    entrypoint = shlex.split(IMAGE_ENTRYPOINT)

    docker_env = ["-e", f"GOFIPS={GOFIPS}"]
    process = docker_util.run_in_docker(
        image, entrypoint, check_exit_code=False, docker_args=docker_env
    )

    rockcraft_yaml = (
        (REPO_PATH / "metallb" / image_version / "controller" / "rockcraft.yaml")
        .read_text()
        .lower()
    )
    expected_returncode, expected_error = fips_util.fips_expectations(
        rockcraft_yaml, GOFIPS
    )

    assert (
        process.returncode == expected_returncode
    ), f"Return code mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
    assert (
        expected_error in process.stderr
    ), f"Error message mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
