# MetalLB FIPS Compliance Analysis

## Overview
This document provides an analysis of MetalLB's cryptographic implementation with respect to FIPS 140 compliance requirements.

Note: As of now, FRR and pebble are not built in a FIPS-compliant way. This document will be updated once they are.

## Cryptographic Implementation Analysis

### Speaker Component
MetalLB's speaker component primarily handles BGP/ARP/NDP protocols and service advertisement. The speaker's cryptographic usage is minimal and focused on:

- Secure communication with the controller (if using the layer 2 mode), see [speaker source](https://github.com/metallb/metallb/blob/main/internal/speakerlist/speakerlist.go#L16)
- BGP session security when configured with authentication (Note: While Metallb allows MD5 it is not FIPS compliant and should be avoided in FIPS mode. MD5 calls will fail on a FIPS-enabled system.)

### Controller Component
The controller handles the Kubernetes API communication and IP address management. Its cryptographic usage includes:

- TLS for secure communication with the Kubernetes API server
- Certificate validation for webhook servers

See [controller source](https://github.com/metallb/metallb/blob/659944f6cfbad3c7ef84fe975aa9811b9821aa57/internal/k8s/k8s.go#L7-L8)

## FIPS Compliance Status

### Implementation

MetalLB's current implementation uses Go's standard `crypto` packages, which are FIPS-compliant when built with the appropriate toolchain. The following requirements must be met:

1. **Go Toolchain**: Must use the modified [Go toolchain from Microsoft](https://github.com/microsoft/go/blob/microsoft/release-branch.go1.23/eng/doc/fips/README.md) that links against FIPS-validated cryptographic modules.
2. **OpenSSL**: Must link against a FIPS-validated OpenSSL implementation, e.g. from `core22/fips`.
3. **Build Environment**: Must be built on an Ubuntu Pro machine with FIPS updates enabled, see below.

### Required Build Modifications

To build MetalLB in FIPS-compliant mode:

1. **Prerequisites**:
   - Ubuntu Pro enabled machine
   - FIPS updates enabled (`sudo pro enable fips-updates`)
   - rockcraft on `edge/pro-sources` channel, see [this discourse post](https://discourse.ubuntu.com/t/build-rocks-with-ubuntu-pro-services/57578)

2. **Build Command**:
   ```bash
   sudo rockcraft pack --pro=fips-updates
   ```
