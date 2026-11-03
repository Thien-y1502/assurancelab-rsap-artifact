# RSAP v2 Docker reproduction

- Image: `assurance-lab-rsap:v2-release`
- Image digest: `sha256:5673738763a9c0bab94dd72bcd6bde499266617d49eaa365ad3b14504d26d948`
- Command: `docker run --rm --network none ... assurance-lab-rsap:v2-release`
- Exit code: `0`
- Result: `DOCKER_PASS_BOUNDED_SIMULATION`

The v2 container replay used the matched-baseline, proof-audit runner from
this packet. This confirms reproducibility of the simulation harness only;
enterprise scheduling remains out of scope.
