# RSAP Docker reproduction

- Image: `assurance-lab-rsap:20261103`
- Image digest: `sha256:f58b0079c828d712c0d29d28ee6e17b53d6ba22488f946bf13c7c541060736fa`
- Base image: `python:3.12-slim` (local cached digest)
- Command: `docker run --rm --network none ... assurance-lab-rsap:20261103`
- Exit code: `0`
- Network: disabled
- Result: `DOCKER_PASS_BOUNDED`

This confirms container replay of the local harness, not enterprise scheduling
effectiveness or independent-host replication.
