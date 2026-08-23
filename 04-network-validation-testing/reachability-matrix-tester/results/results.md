# Reachability Matrix Tester — Results

- Total: **5** · pass **3** · violation **1** · ambiguous **1**

| Intent | Expected | Verdict | Status | Reason |
|---|---|---|---|---|
| `engineering-to-servers-tcp` | permit | permit | pass | — |
| `guest-to-servers-blocked` | deny | deny | pass | — |
| `unlisted-subnet-should-be-denied` | deny | permit | violation | — |
| `engineering-to-specific-server-tcp` | permit | permit | pass | — |
| `broad-engineering-supernet-query` | permit | mixed | ambiguous | rule 10 only partially overlaps the queried range |
