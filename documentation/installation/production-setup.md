# **📌 Advanced Deployment Guide: Rancher RKE, Kubernetes Fleet & MinIO on Rocky Linux**

## **🛠 Overview**

This guide provides an advanced methodology for deploying **Rancher RKE, Kubernetes Fleet, and MinIO** within a lightweight, high-performance **Rocky Linux** environment, optimized for VirtualBox-based virtualization.

### **🌍 Deployment Components**

✅ **Rocky Linux Virtual Machines** (Minimal Installation for optimal performance)   
✅ **Rancher Server (Fleet Manager)** for centralized Kubernetes governance   
✅ **Rancher Kubernetes Engine (RKE)** for robust Kubernetes cluster management   
✅ **Multi-node Kubernetes Cluster Architecture**   
✅ **Rancher Fleet for GitOps-based multi-cluster orchestration**   
✅ **MinIO for high-performance, distributed object storage**   
✅ **Cloudflare for resilient load balancing and security enforcement**   

---

## **🛠 Optimal Operating System Selection**
For an enterprise-grade Kubernetes environment, selecting an OS with **stability, lightweight footprint, and long-term support** is paramount. Below is a comparative analysis of the most suitable distributions:

| **OS**                 | **Base System** | **RAM Usage (Idle)** | **Rationale for Selection** |
|------------------------|---------------|----------------|----------------|
| **Rocky Linux Minimal** | RHEL-based | **~250MB** | ✅ Optimal CentOS replacement with enterprise support. |
| **AlmaLinux Minimal** | RHEL-based | **~250MB** | ✅ Functionally identical to Rocky Linux, with CloudLinux backing. |
| **Debian Minimal (Netinst)** | Debian | **~200MB** | ✅ Highly stable, efficient package management. |
| **Ubuntu Server Minimal** | Ubuntu | **~300MB** | ✅ Officially supported by Rancher, albeit slightly resource-intensive. |

🚀 **Recommended OS:** **Rocky Linux Minimal 9.5** ([Download Here](https://rockylinux.org/download))

---

## **1️⃣ Virtual Machine Configuration & Rocky Linux Installation**

Given our VirtualBox-based deployment, the following VM specifications ensure **high availability while conserving resources**:

| **VM Name**      | **Role**                    | **CPU** | **RAM** | **Disk** |
| ---------------- | --------------------------- | ------- | ------- | -------- |
| `rancher-master` | Rancher Server & K8s Control Plane | 2       | 2GB     | 20GB     |
| `worker-1`       | Kubernetes Worker Node      | 1       | 1.5GB   | 15GB     |
| `worker-2`       | Kubernetes Worker Node      | 1       | 1.5GB   | 15GB     |

### **1️⃣ Install Rocky Linux Minimal on Each VM**

1. **Download Rocky Linux Minimal ISO** → [rockylinux.org/download](https://rockylinux.org/download)

2. **Create VirtualBox VMs** → Configure CPU, RAM, and Disk according to the table above.

3. **Set VM Network to Bridged Mode** to allow internet access.
   - If `Bridged Mode` does not work, try switching to another adapter (e.g., `NAT`) in VirtualBox VM settings.

4. **Perform a Minimal Installation (CLI-only, no GUI).**

5. **Update System Packages:**

   ```sh
   sudo dnf update -y && sudo dnf install -y curl wget git vim
   ```

6. **Enable Internet Connection:**
   ```sh
   sudo nmcli connection up enp0s3
   ```
   - If `enp0s3` does not work, check the correct interface with:
     ```sh
     nmcli device status
     ```
   - If another interface is listed (e.g., `eth0`), use that instead:
     ```sh
     sudo nmcli connection up eth0
     ```
   
   Verify internet connectivity:
   ```sh
   ping google.com
   ```

7. **Assign Hostnames for Network Identification:**

   ```sh
   sudo hostnamectl set-hostname rancher-master
   ```

   (Repeat the above step for `worker-1` and `worker-2`.)

---

## **2️⃣ Deploying Rancher Server**

### **1️⃣ Install Docker on `rancher-master`**

```sh
sudo dnf install -y yum-utils
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

📌 **Reboot the VM to ensure changes take effect.**

### **2️⃣ Deploy Rancher Server via Docker**

```sh
docker run -d --restart=unless-stopped \
  -p 80:80 -p 443:443 \
  --privileged \
  rancher/rancher:latest
```

✔ The Rancher UI will be accessible at **`https://<RANCHER_VM_IP>`**.

---

