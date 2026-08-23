# Config Intent Checker — Results

- Intents checked: **8**
- Passed: **4**

| Intent | Passed | Reason |
|---|---|---|
| `{"type": "interface_access_vlan", "interface": "GigabitEthernet0/1", "vlan": 20}` | True | — |
| `{"type": "interface_access_vlan", "interface": "GigabitEthernet0/3", "vlan": 30}` | True | — |
| `{"type": "interface_access_vlan", "interface": "GigabitEthernet0/3", "vlan": 10}` | False | found switchport access vlan 30, expected 10 |
| `{"type": "interface_access_vlan", "interface": "GigabitEthernet0/2", "vlan": 10}` | False | interface GigabitEthernet0/2 is not in access mode |
| `{"type": "interface_access_vlan", "interface": "GigabitEthernet0/9", "vlan": 5}` | False | interface GigabitEthernet0/9 not found in config |
| `{"type": "line_present", "pattern": "^hostname\\s+sw1$"}` | True | — |
| `{"type": "line_present", "pattern": "^ip domain-name\\s+example\\.com$"}` | True | — |
| `{"type": "line_present", "pattern": "^ntp server "}` | False | no line matching pattern '^ntp server ' found in config |
