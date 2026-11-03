# RSAP baseline roles

- `uniform_eprocess`: fixed cyclic query order with the same anytime certificate.
- `greedy_cost`: lowest-cost query with naive five-observation stopping.
- `risk_score_naive`: fixed risk/cost ranking with naive stopping.
- `peek_stop`: low-cost query with optional-stopping window rule.
- `RSAP`: predictable adaptive action selection plus AssuranceLab
  `AnytimeCertificate` and full policy trace.

The comparison separates the selection policy from the risk-control certificate;
the result is not a reward-only RL claim.
