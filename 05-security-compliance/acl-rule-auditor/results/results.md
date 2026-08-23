# ACL Rule Audit Results

- Device: **edge-fw-01**
- ACLs/rules: **2 / 7**
- Findings: **5**

| ACL | Seq | Type | Severity | Detail |
|---|---:|---|---|---|
| OUTSIDE_IN | 20 | shadowed | medium | Fully covered by sequence 10 (permit) |
| OUTSIDE_IN | 20 | unused | low | No hits for 91 days |
| OUTSIDE_IN | 30 | any-any-permit | critical | Permits all IPv4 traffic |
| OUTSIDE_IN | 40 | shadowed | high | Fully covered by sequence 30 (permit) |
| MGMT_IN | 20 | unused | low | No hits for 120 days |
