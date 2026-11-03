# RSAP v2 independent-proof and robustness results

All policies use the same pre-generated uniform streams, action space, seed
blocks and budget. Certificate-bearing policies use the same `AnytimeCertificate`
implementation; this isolates action-selection effects from certificate choice.

| Policy | Unsafe false PASS | Wilson upper | Safe coverage | Median cost |
|---|---:|---:|---:|---:|
| RSAP | 0.0002 | 0.00113 | 1.0000 | 27.0 |
| Risk-score e-process | 0.0002 | 0.00113 | 1.0000 | 27.0 |
| Uniform e-process | 0.0000 | 0.00077 | 0.9996 | 37.0 |
| Random e-process | 0.0002 | 0.00113 | 1.0000 | 40.0 |
| Risk-score naive | 0.1610 | 0.17145 | 0.9986 | 5.0 |
| Greedy cost | 0.1610 | 0.17145 | 0.9986 | 5.0 |

RSAP minus uniform median-cost difference is negative with an across-seed
confidence interval entirely below zero. The safe-coverage difference is
compatible with zero and never below the declared comparator in the aggregate.

The nine-point budget/loss-shift sensitivity grid keeps the false-PASS upper
bound below 0.05 and has zero budget exceedance. A 1,024-sequence implementation
audit has zero wealth disagreements, and the predictable-factor expectation
checks pass at every tested lambda.
