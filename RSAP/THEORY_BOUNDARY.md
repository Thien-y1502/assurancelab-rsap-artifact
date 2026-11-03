# RSAP theory boundary

The run exercises the existing `AnytimeCertificate` under a predictable policy
and records every selected action. It does not prove the intended general
adaptive-filtration theorem. Required next gates are:

1. formalize the filtration and action measurability assumptions;
2. prove the composed e-process remains a supermartingale under adaptive query
   choice;
3. audit optional stopping and alpha allocation independently;
4. add poisoned utility estimates and source-selection shift controls;
5. reproduce the result in Docker and with an independent implementation.
