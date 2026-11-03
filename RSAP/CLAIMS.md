# RSAP claim ledger

## Supported by this run

- `SUPPORTED_BOUNDED`: unsafe false-PASS rate 0.0002 with Wilson upper bound
  0.00113 under the frozen synthetic model.
- `SUPPORTED_BOUNDED`: safe PASS coverage 1.0000 and median decision cost 27,
  lower than uniform e-process at 37.
- `SUPPORTED_BOUNDED`: every episode had a complete policy trace and no budget
  exceedance.

## Not supported

- `UNPROVEN`: general optional-stopping theorem for arbitrary adaptive query
  policies.
- `NOT_TESTED`: external audit connectors, enterprise downtime, Docker replay,
  cross-host independence, or production cost model.
- `UNRESOLVED`: superiority over source-faithful external schedulers.
