# MetalLB FIPS Compliance

For comprehensive information about FIPS 140-3 compliance in Canonical Kubernetes, including how ROCKs are built with FIPS support, please refer to the [k8s-snap FIPS documentation](https://github.com/canonical/k8s-snap/blob/main/docs/dev/fips.md).

> **Note:** As of now, FRR and pebble are not built in a FIPS-compliant way. This document will be updated once they are.

## MetalLB-Specific Information

### BGP Authentication and FIPS

While MetalLB allows MD5 authentication for BGP sessions, **MD5 is not FIPS-compliant** and should be avoided in FIPS mode. MD5 authentication calls will fail on a FIPS-enabled system.

### FRR Mode

FRR mode is not FIPS-compliant. However, enabling FRR mode is not supported in Canonical Kubernetes, so this does not impact FIPS compliance for users of that Kubernetes distribution.

### Component Details

#### Speaker Component

MetalLB's speaker component primarily handles BGP/NDP protocols and service advertisement. The speaker's cryptographic usage is minimal and focused on:

- Secure communication with the controller (if using the layer 2 mode)
- BGP session security when configured with authentication (Note: MD5 authentication is not FIPS-compliant)

See [speaker source](https://github.com/metallb/metallb/blob/main/internal/speakerlist/speakerlist.go#L16).

#### Controller Component

The controller handles the Kubernetes API communication and IP address management. Its cryptographic usage includes:

- TLS for secure communication with the Kubernetes API server
- Certificate validation for webhook servers

See [controller source](https://github.com/metallb/metallb/blob/659944f6cfbad3c7ef84fe975aa9811b9821aa57/internal/k8s/k8s.go#L7-L8).
