# MetalLB FIPS Compliance

For comprehensive information about FIPS 140-3 compliance in Canonical Kubernetes, including how ROCKs are built with FIPS support, please refer to the [k8s-snap FIPS documentation](https://github.com/canonical/k8s-snap/blob/main/docs/dev/fips.md).

> **Note:** As of now, pebble is not built in a FIPS-compliant way. This document will be updated once it is.

## BGP Authentication and FIPS

While MetalLB allows MD5 authentication for BGP sessions, **MD5 is not FIPS-compliant** and should be avoided in FIPS mode. MD5 authentication calls will fail on a FIPS-enabled system.

## FRR Mode

As of `frr/10.4.1`, the FRR rock is built with `--with-crypto=openssl` and
stages `openssl-fips-module-3` (see [rockcraft.yaml](../frr/10.4.1/rockcraft.yaml)),
so BFD keyed-SHA1 authentication (`HMAC-SHA1` via OpenSSL,
[bfd_packet.c](https://github.com/FRRouting/frr/blob/88f5c06cbc1cc4d62e1cba3e7791f5cea4179ba5/bfdd/bfd_packet.c#L29-L31))
now dynamically links against the Pro FIPS-validated OpenSSL module at runtime.

Two caveats remain:

- BFD authentication is capped at keyed-SHA1 or cleartext by FRR itself
  ([bfd.c#L667-L670](https://github.com/FRRouting/frr/blob/88f5c06cbc1cc4d62e1cba3e7791f5cea4179ba5/bfdd/bfd.c#L667-L670));
  SHA-256/384/512 key-chain entries are never selected for BFD sessions.
- MetalLB's `BFDProfile` CRD has no field to attach a key-chain to a BFD
  session, so this capability is not yet reachable through MetalLB's own
  configuration surface. Enabling it requires upstream MetalLB changes to the
  `BFDProfile` API and FRR config template, not just the rock build.
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
