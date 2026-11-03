# AssuranceLab RSAP v2 artifact

Reproducibility repository for the **Risk-bounded Selective Audit Policy
(RSAP)** independent-proof/robustness simulation v2.

RSAP evaluates selective evidence acquisition with an anytime certificate and
compares it with uniform e-process and simple cost/risk baselines.

## What is included

- `RSAP/EXPERIMENT_CONTRACT_V2.json` — frozen matched-baseline contract.
- `RSAP/run_rsap_v2.py` — deterministic local runner.
- `RSAP/results.json` — executed v2 result and claim boundary.
- `RSAP/raw_episodes_v2.jsonl` — generated episode-level traces.
- `RSAP/BASELINES.md`, `RSAP/THEORY_BOUNDARY.md`, `RSAP/REDTEAM.md`.
- `src/assurance_lab/` — source snapshot used by the runner.
- `RSAP/Dockerfile` — network-disabled container replay.
- `MANIFEST.sha256` — file-integrity manifest.

## Reproduce locally

Python 3.12 is the reference runtime and the runner has no third-party
dependencies.

```bash
python RSAP/run_rsap_v2.py
python -c "import json; print(json.load(open('RSAP/results.json'))['status'])"
```

Expected status: `PASS` with claim state `BOUNDED_SIMULATION_PASS`.

## Reproduce in Docker

```bash
docker build --pull=false -f RSAP/Dockerfile -t assurancelab-rsap-artifact .
docker run --rm --network none assurancelab-rsap-artifact
```

The run uses five seeds × 1,000 safe and 1,000 unsafe episodes per policy.
The container replay is an execution/reproducibility check, not enterprise
scheduling validation or proof of the general adaptive-filtration theorem.

## Scientific boundary

The bounded result reports false-PASS control, safe coverage and acquisition
cost on generated episodes. It does not establish a general theorem,
external-baseline superiority on every workload, or enterprise utility. See
`RSAP/CLAIMS.md` before citing results.

## License and citation

Code and artifact metadata are released under Apache-2.0. Cite the associated
paper only after acceptance; until then, cite the repository commit and
`MANIFEST.sha256`.
