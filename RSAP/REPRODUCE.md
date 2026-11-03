# RSAP reproduction

From the repository root:

```powershell
python handoff\q1_execution_2026-11-03\RSAP\run_rsap.py
python handoff\q1_execution_2026-11-03\RSAP\run_rsap_v2.py
```

The command writes `raw_episodes.jsonl` and `results.json`. The runner imports
the local `AnytimeCertificate`, records the Docker probe, and retains the full
selection trace for every episode.
