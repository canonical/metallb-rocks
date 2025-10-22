# MetalLB FIPS compliance analysis

The following document summarizes the current state of [FIPS 140-3] compliance
for MetalLB, focusing on its cryptographic components and build requirements.
This overview is intended to guide users and developers in understanding the
compliance status and necessary steps for achieving FIPS mode operation.

> **Note:** As of now, FRR and pebble are not built in a FIPS-compliant way. This document will be updated once they are.

## Abbreviations

This document uses a set of abbreviations which are explained below:

- **Federal Information Processing Standards (FIPS)**: A set of standards for
cryptographic modules published by the U.S. government.
- **Border Gateway Protocol (BGP)**: A standardized exterior gateway protocol for
exchanging routing information between autonomous systems on the internet.
- **Federal Information Processing Standards (FIPS)**: A set of standards for
cryptographic modules published by the U.S. government.
- **Transport Layer Security (TLS)**: A cryptographic protocol designed to provide
secure communication over a computer network.
- **Open Source Routing Software (FRR)**: A routing software suite used for network
routing protocols.
- **Network Discovery Protocol (NDP)**: A protocol in the IPv6 suite for neighbor
discovery.
- **Advanced Package Tool (APT)**: A package management system used by
Debian-based Linux distributions.

## Cryptographic implementation analysis

MetalLB's cryptographic footprint is limited and primarily involves secure
communication between components and with the Kubernetes API. The speaker uses
minimal cryptography, mainly for BGP authentication and communication with the
controller, while the controller relies on TLS for Kubernetes API interactions.
FIPS compliance depends on the cryptographic libraries and build environment
used for these components.

### Speaker Component

MetalLB's speaker component primarily handles BGP/NDP protocols and service
advertisement. The speaker's cryptographic usage is minimal and focused on:

- Secure communication with the controller (if using the layer 2 mode), see
[speaker source]
- BGP session security when configured with authentication (Note: While Metallb
allows MD5 it is not FIPS compliant and should be avoided in FIPS mode. MD5
calls will fail on a FIPS-enabled system.)

### Controller Component

The controller handles the Kubernetes API communication and IP address
management. Its cryptographic usage includes:

- TLS for secure communication with the Kubernetes API server
- Certificate validation for webhook servers

See [controller source]

## FIPS Compliance Status

### Implementation

MetalLB's current implementation uses Go's standard `crypto` packages, which are
FIPS-compliant when built with the appropriate toolchain. The following
requirements must be met:

1. **Go Toolchain**: Must use the modified [Go toolchain from Microsoft]
2. **OpenSSL**: Must link against a FIPS-validated OpenSSL implementation,
there is no fips base yet for rocks so e.g. from `core22/fips`.
3. **Build Environment**: Must be built on an Ubuntu Pro machine, see below.

### Required Build Modifications

To build MetalLB in FIPS-compliant mode:

1. **Prerequisites**:
   - Ubuntu Pro enabled machine
   - FIPS **not** enabled
   - rockcraft on `edge/pro-sources` channel, see [this discourse post]

2. **Build Command**:

   ```bash
   sudo rockcraft pack --pro=fips-updates
   ```

## Python FIPS compliance

FRR includes Python dependencies and scripting support (python3-dev,
python3-sphinx), making Python FIPS compliance relevant to the MetalLB
ecosystem.

Python FIPS compliance requires using system OpenSSL for cryptographic
operations over non-FIPS compliant algorithms.

Python links to the system OpenSSL by default. On a FIPS-enabled host,
algorithms that use the OpenSSL implementation will be FIPS compliant.
However, Python contains builtin
hashing algorithms that are not FIPS compliant (e.g. [MD5]). Building Python
with `--without-builtin-hashlib-hashes` will remove these non-FIPS compliant
algorithms.

In order to confirm Python is referencing the system OpenSSL, run the following
command to find the location of the _ssl module:

```
python3 -c 'import _ssl; print(_ssl.__file__)'
```

You will get an output similar to this:

```
/usr/lib/python3.13/lib-dynload/_ssl.cpython-313-x86_64-linux-gnu.so
```

Run [ldd] to print the shared libraries and look for libssl.so and
libcrypto.so:

```
ldd /usr/lib/python3.13/lib-dynload/_ssl.cpython-313-x86_64-linux-gnu.so | grep -E 'libssl|libcrypto'
```

The output should be similar to this:
```
libssl.so.3 => /lib/x86_64-linux-gnu/libssl.so.3 (0x000075b68a51f000)
libcrypto.so.3 => /lib/x86_64-linux-gnu/libcrypto.so.3 (0x000075b689e00000)
```

In cases where your output does not show the system's libssl and libcrypto,
you need to ensure that your [ROCK] or docker image is either built with a
FIPS-compliant OpenSSL, or is referencing the host's OpenSSL.

<!-- LINKS -->

[FIPS 140-3]: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.140-3.pdf
[ldd]: https://man7.org/linux/man-pages/man1/ldd.1.html
[ROCK]: https://documentation.ubuntu.com/rockcraft/stable/explanation/rocks/
[speaker source]: https://github.com/metallb/metallb/blob/main/internal/speakerlist/speakerlist.go#L16
[controller source]: https://github.com/metallb/metallb/blob/659944f6cfbad3c7ef84fe975aa9811b9821aa57/internal/k8s/k8s.go#L7-L8
[Go toolchain from Microsoft]: https://github.com/microsoft/go/blob/microsoft/release-branch.go1.23/eng/doc/fips/README.md
[this discourse post]: https://discourse.ubuntu.com/t/build-rocks-with-ubuntu-pro-services/57578
