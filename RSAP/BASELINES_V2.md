# RSAP v2 baseline fairness

All policies see identical pre-generated uniform streams for each seed,
episode and safe/unsafe state. They use the same five actions, costs, budget,
episode count and stopping horizon.

- `uniform_eprocess`, `random_eprocess` and `risk_score_eprocess` use the same
  certificate and differ only in action selection.
- `risk_score_naive` and `greedy_cost` retain naive five-observation stopping
  to show the cost/safety trade-off when the certificate is removed.
- RSAP is compared primarily with `uniform_eprocess` and `risk_score_eprocess`
  so the policy effect is not confused with certificate effect.

The packet reports paired across-seed differences rather than comparing
unpaired means. External schedulers remain a manuscript-stage extension, not a
hidden claim of superiority.
