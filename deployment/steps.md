# **🚀 MinIO, Django, and Nginx Setup with GeoIP-Based Routing**

## **📌 Step 1: MinIO Configuration**
### **1️⃣ Set MinIO Aliases**
```sh
mc alias set site1 http://localhost:9000 admin admin123
mc alias set site2 http://localhost:9010 admin admin123
```

### **2️⃣ Verify MinIO Status**
```sh
mc admin info site1
mc admin info site2
```

### **3️⃣ Create Buckets for Replication**
```sh
mc mb site1/drive
mc mb site2/drive
```

### **4️⃣ Enable Replication Between Site 1 and Site 2**
```sh
mc replicate add site1/drive --remote-bucket http://admin:admin123@172.18.0.9:9000/drive --priority 1 --replicate "delete-marker,delete,existing-objects,metadata-sync"

mc replicate add site2/drive --remote-bucket http://admin:admin123@172.18.0.5:9000/drive --priority 1 --replicate "delete-marker,delete,existing-objects,metadata-sync"
```

### **5️⃣ Verify Replication Status**
```sh
mc admin replicate status site1
mc admin replicate status site2
```

### **6️⃣ Test Replication**
```sh
mc cp testfile.txt site1/drive
mc ls site2/drive
```

---

## **📌 Step 2: Debugging MinIO Issues**
### **1️⃣ Check Running Containers**
```sh
docker ps
```

### **2️⃣ Check MinIO Logs**
```sh
docker logs site1-minio1-1 --tail=50
docker logs site2-minio1-1 --tail=50
```

### **3️⃣ Check If MinIO Drives Are Mounted**
```sh
docker exec -it site1-minio1-1 sh -c "ls -lah /data"
docker exec -it site2-minio1-1 sh -c "ls -lah /data"
```

### **4️⃣ Fix Missing Volumes**
```sh
docker volume ls
docker volume create site1_data1
docker volume create site2_data1
```

### **5️⃣ Clean Up and Restart MinIO**
```sh
docker compose down -v
docker volume prune -f
docker compose up -d
```

---

## **📌 Step 3: Django Setup**
### **1️⃣ Start Django Containers**
```sh
docker compose up -d
```

### **2️⃣ Check Running Django Containers**
```sh
docker ps | grep django
```

### **3️⃣ Verify Django Logs**
```sh
docker logs site1-django --tail=50
docker logs site2-django --tail=50
```

---

## **📌 Step 4: Nginx Setup for GeoIP Routing**
### **1️⃣ Build & Start Nginx**
```sh
docker compose up -d --build
```

### **2️⃣ Check Running Nginx Containers**
```sh
docker ps | grep nginx
```

### **3️⃣ Verify Nginx Logs for Errors**
```sh
docker logs nginx-load-balancer --tail=50
```

### **4️⃣ Test Django Routing (Expected: Routes to 3000 or 3001)**
```sh
curl -H "X-Real-IP: 8.8.8.8" http://localhost/
curl -H "X-Real-IP: 5.9.9.9" http://localhost/
```

### **5️⃣ Test MinIO Routing (Expected: Routes to 9000)**
```sh
curl -H "X-Real-IP: 8.8.8.8" http://localhost/s3/
curl -H "X-Real-IP: 5.9.9.9" http://localhost/s3/
```

### **6️⃣ Check If GeoIP2 Module Is Loaded**
```sh
docker exec -it nginx-load-balancer sh -c "nginx -V 2>&1 | grep geoip2"
```

---

## **📌 Step 5: Fixing Common Issues**
### **1️⃣ Fix "Access Denied" in MinIO**
```sh
mc alias set site1 http://localhost:9000 admin admin123
mc admin policy set site1 readwrite user=admin
```

### **2️⃣ Fix "Unknown Directive `geoip2`" in Nginx**
```sh
docker exec -it nginx-load-balancer sh -c "ls /etc/nginx/modules/"
```

### **3️⃣ Fix Nginx Default Page Issue**
```sh
rm -rf /usr/share/nginx/html/*
```

---

## **🎯 Final Summary**
| **Step** | **Command** | **Purpose** |
|----------|------------|-------------|
| **Set MinIO alias** | `mc alias set site1 http://localhost:9000 admin admin123` | Connect `mc` to MinIO |
| **Check MinIO status** | `mc admin info site1` | Ensure MinIO is running |
| **Create buckets** | `mc mb site1/drive` | Create MinIO bucket |
| **Enable replication** | `mc replicate add site1/drive ...` | Set up MinIO replication |
| **Check logs** | `docker logs site1-minio1-1 --tail=50` | Debug MinIO issues |
| **Start Django containers** | `docker compose up -d` | Start Django apps |
| **Check Django logs** | `docker logs site1-django --tail=50` | Debug Django issues |
| **Rebuild & restart Nginx** | `docker compose up -d --build` | Apply Nginx changes |
| **Check Nginx logs** | `docker logs nginx-load-balancer --tail=50` | Debug Nginx issues |
| **Test routing** | `curl -H "X-Real-IP: 8.8.8.8" http://localhost/` | Check GeoIP routing |
| **Fix MinIO access** | `mc admin policy set site1 readwrite user=admin` | Fix MinIO access issues |

🚀 **Now, everything is fully configured, and you have all the necessary commands for debugging and fixing issues!** 🎯