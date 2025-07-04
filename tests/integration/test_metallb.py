#
# Copyright 2025 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness import harness
from k8s_test_harness.util import constants, env_util, k8s_util
from k8s_test_harness.util.k8s_util import HelmImage

IMG_PLATFORM = "amd64"
INSTALL_NAME = "metallb"


def _get_rock_image(name: str, version: str):
    rock = env_util.get_build_meta_info_for_rock_version(name, version, IMG_PLATFORM)
    return rock.image


@pytest.mark.parametrize(
    "metallb_version,frr_version",
    [("v0.14.5", "9.0.2"), ("v0.14.8", "9.1.0"), ("v0.14.9", "9.1.3")],
)
def test_metallb(
    function_instance: harness.Instance, metallb_version: str, _: str
):
    images = [
        HelmImage(
            uri=_get_rock_image("metallb-controller", metallb_version),
            prefix="controller",
        ),
        HelmImage(
            uri=_get_rock_image("metallb-speaker", metallb_version), prefix="speaker"
        ),
    ]

    # We need to run frr as root because of:
    # https://bugzilla.redhat.com/show_bug.cgi?id=2147522
    helm_command = k8s_util.get_helm_install_command(
        name=INSTALL_NAME,
        chart_name="metallb",
        images=images,
        namespace=constants.K8S_NS_KUBE_SYSTEM,
        repository="https://metallb.github.io/metallb",
        chart_version=metallb_version,
        runAsUser=0,
    )
    helm_command += [
        "--set",
        "controller.securityContext.fsGroup=0",
        "--set",
        "controller.securityContext.runAsNonRoot=false",
        "--set",
        "controller.command=/controller",
        "--set",
        "speaker.command=/speaker",
        "--set",
        # Note(ben): Enable once we also use it in CK8s
        "frr.enabled=false",
    ]
    function_instance.exec(helm_command)

    k8s_util.wait_for_daemonset(
        function_instance, "metallb-speaker", constants.K8S_NS_KUBE_SYSTEM
    )

    k8s_util.wait_for_deployment(
        function_instance, "metallb-controller", constants.K8S_NS_KUBE_SYSTEM
    )
