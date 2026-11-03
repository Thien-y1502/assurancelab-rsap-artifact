# RSAP bounded local results

The current release result is v2; see `RESULTS_V2.md` and
`EXPERIMENT_CONTRACT_V2.json`. The v1 table below is retained as historical
evidence.

Run: five seeds × 1,000 safe and 1,000 unsafe episodes per policy. The budget
is 80 cost units and the false-PASS alpha target is 0.05.

| Policy | Unsafe false PASS | Wilson upper bound | Safe PASS coverage | Median cost | Budget exceeded |
|---|---:|---:|---:|---:|---:|
| RSAP | 0.0002 | 0.00113 | 1.0000 | 27.0 | 0 |
| Uniform e-process | 0.0000 | 0.00077 | 0.9996 | 37.0 | 0 |
| Risk-score naive | 0.1634 | 0.17391 | 0.9984 | 5.0 | 0 |
| Greedy cost | 0.1586 | 0.16899 | 0.9992 | 5.0 | 0 |
| Peek-stop | 0.1656 | 0.17616 | 0.9996 | 5.0 | 0 |

The local contract is satisfied: RSAP remains below the predeclared false-PASS
bound, retains safe coverage at least as high as uniform e-process, and reduces
median cost relative to uniform e-process. This is bounded synthetic evidence,
not a general theorem or enterprise scheduling result.
