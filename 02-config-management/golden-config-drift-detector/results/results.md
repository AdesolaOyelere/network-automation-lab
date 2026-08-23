# Golden Configuration Drift Results

- Device: **branch-rtr-01**
- In sync: **False**

| Class | Count |
|---|---:|
| changed | 2 |
| missing | 0 |
| unexpected | 5 |

## Changed

- `interface GigabitEthernet0/0`: `description WAN uplink - carrier A` → `description WAN uplink - carrier B`
- `interface GigabitEthernet0/1`: `ip helper-address 10.99.0.10` → `ip helper-address 10.99.0.20`

## Missing

None.

## Unexpected

- `global`: `interface GigabitEthernet0/2`
- `interface GigabitEthernet0/2`: `description Temporary lab`
- `interface GigabitEthernet0/2`: `ip address 10.30.0.1 255.255.255.0`
- `interface GigabitEthernet0/2`: `no shutdown`
- `router ospf 10`: `network 10.30.0.0 0.0.0.255 area 0`
