# MetalLB FIPS Compliance

For comprehensive information about FIPS 140-3 compliance in Canonical Kubernetes, including how ROCKs are built with FIPS support, please refer to the [k8s-snap FIPS documentation](https://github.com/canonical/k8s-snap/blob/main/docs/dev/fips.md).

> **Note:** As of now, pebble is not built in a FIPS-compliant way. This document will be updated once it is.

## BGP Authentication and FIPS

While MetalLB allows MD5 authentication for BGP sessions, **MD5 is not FIPS-compliant** and should be avoided in FIPS mode. MD5 authentication calls will fail on a FIPS-enabled system.

## FRR Mode

As of `frr/10.4.1`, the FRR rock is built with `--with-crypto=openssl` and
stages `openssl-fips-module-3` (see [rockcraft.yaml](../frr/10.4.1/rockcraft.yaml)).
This makes OSPF, RIPv2, and IS-IS's existing keyed MD5/SHA authentication
FIPS-compliant (`ospfd/ospf_auth.c`, `ospf6d/ospf6_auth_trailer.c`,
`ripd/ripd.c`, `isisd/isis_tlvs.c` all gate their auth implementation behind
`CRYPTO_OPENSSL`) by dynamically linking those daemons against the Pro
FIPS-validated OpenSSL module at runtime.

Caveats:

- **BFD authentication is unimplemented in FRR 10.4.1**, independent of this
  fix: `bfdd/bfd_packet.c`'s `bfd_check_auth()` unconditionally returns
  `false` for both `BFD_AUTH_SIMPLE` and `BFD_AUTH_CRYPTOGRAPHIC`, per an
  upstream TODO comment marking RFC5880 Section 6.7 auth handling as
  unimplemented, and `--with-crypto=openssl` has no effect on `bfdd` on
  this version (`CRYPTO_OPENSSL` is never referenced under `bfdd/` in
  10.4.1). BFD keychain auth only lands in FRR 10.7.0+ — see the
  `frr/10.7.1` rock.
- MetalLB's `BFDProfile` CRD has no field to attach a key-chain to a BFD
  session either way, so BFD auth is not reachable through MetalLB's own
  configuration surface regardless of FRR version. Enabling it requires
  upstream MetalLB changes to the `BFDProfile` API and FRR config template.
- BGP MD5 (`neighbor ... password`) remains **not** FIPS-compliant — see
  "BGP Authentication and FIPS" above.

## Speaker

MetalLB's speaker component primarily handles BGP/NDP protocols and service advertisement. The speaker's cryptographic usage is minimal and focused on:

- Secure communication with the controller (if using the layer 2 mode)
- BGP session security when configured with authentication (Note: MD5 authentication is not FIPS-compliant)

See [speaker source](https://github.com/metallb/metallb/blob/main/internal/speakerlist/speakerlist.go#L16).

## Controller

The controller handles the Kubernetes API communication and IP address management. Its cryptographic usage includes:

- TLS for secure communication with the Kubernetes API server
- Certificate validation for webhook servers

See [controller source](https://github.com/metallb/metallb/blob/659944f6cfbad3c7ef84fe975aa9811b9821aa57/internal/k8s/k8s.go#L7-L8).
