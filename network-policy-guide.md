# Kubernetes NetworkPolicy Solution Guide

## Requirements:
1. Allow incoming connections from a namespace where the label 'project' is 'myapp'
2. Block incoming connections from CIDR range 172.10.0.0/16 except 172.10.1.0/24
3. Allow egress connection on port 5687

## Solution Breakdown:

### 1. Namespace Selector (Requirement 1)
```yaml
- from:
    - namespaceSelector:
        matchLabels:
          project: myapp
```
**Explanation:** This allows ingress traffic from any pod in a namespace that has the label `project: myapp`.

### 2. IP Block with Exception (Requirement 2)
```yaml
- from:
    - ipBlock:
        cidr: 172.10.0.0/16
        except:
          - 172.10.1.0/24
```
**Explanation:** 
- The `ipBlock` with `cidr: 172.10.0.0/16` allows traffic from the entire 172.10.0.0/16 range
- The `except` field excludes 172.10.1.0/24 from this allowed range
- **Result:** Traffic from 172.10.0.0/16 is allowed EXCEPT from 172.10.1.0/24 (which is blocked)

**Note:** If the requirement means "block 172.10.0.0/16 but allow 172.10.1.0/24", you would instead use:
```yaml
- from:
    - ipBlock:
        cidr: 172.10.1.0/24
```
(Just allow 172.10.1.0/24 explicitly, and don't include the rest of 172.10.0.0/16)

### 3. Egress Port (Requirement 3)
```yaml
egress:
  - to:
      - ipBlock:
          cidr: 0.0.0.0/0
    ports:
      - protocol: TCP
        port: 5687
```
**Explanation:** This allows egress traffic to any destination (0.0.0.0/0) but only on port 5687 using TCP protocol.

## Complete YAML:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mynetpol
  namespace: default
spec:
  podSelector:
    matchLabels:
      type: sample-test
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              project: myapp
    - from:
        - ipBlock:
            cidr: 172.10.0.0/16
            except:
              - 172.10.1.0/24
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 5687
```

## Dropdown Selections (Based on Images):

1. **First ingress `from` dropdown:** Select `namespaceSelector`
2. **Second ingress `from` dropdown:** Select `ipBlock`
3. **For the exception field:** The dropdown should show `except` (to exclude 172.10.1.0/24)
4. **Egress `to` dropdown:** Select `ipBlock` (for allowing traffic to any destination)
