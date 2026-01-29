# Kubernetes Cluster Upgrade Steps (1.18.0 → 1.19.0)

## Correct Order of Commands:

### Step 1: Drain the master node
```bash
kubectl drain master-node --ignore-daemonsets
```
**Purpose:** Safely evict all pods from the master node before upgrading. The `--ignore-daemonsets` flag is necessary because DaemonSets cannot be evicted.

---

### Step 2: Upgrade kubeadm
```bash
apt-get install -y --allow-change-held-packages kubeadm=1.19.0-00
```
**Purpose:** Upgrade kubeadm to version 1.19.0 first. Kubeadm must be upgraded before it can upgrade the cluster.

---

### Step 3: Plan and apply the upgrade
```bash
sudo kubeadm upgrade plan; sudo kubeadm upgrade apply v1.19.0
```
**Purpose:** 
- `kubeadm upgrade plan` checks what will be upgraded
- `kubeadm upgrade apply v1.19.0` performs the actual cluster upgrade

---

### Step 4: Upgrade kubelet and kubectl
```bash
apt-get install -y --allow-change-held-packages kubelet=1.19.0-00 kubectl=1.19.0-00
```
**Purpose:** Upgrade kubelet (the node agent) and kubectl (the CLI tool) to match the new cluster version.

---

### Step 5: Uncordon the master node
```bash
kubectl uncordon master-node
```
**Purpose:** Mark the node as schedulable again, allowing pods to be scheduled back onto it.

---

## Summary of Correct Order:
1. `kubectl drain master-node --ignore-daemonsets`
2. `apt-get install -y --allow-change-held-packages kubeadm=1.19.0-00`
3. `sudo kubeadm upgrade plan; sudo kubeadm upgrade apply v1.19.0`
4. `apt-get install -y --allow-change-held-packages kubelet=1.19.0-00 kubectl=1.19.0-00`
5. `kubectl uncordon master-node`
