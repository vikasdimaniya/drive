# MyDrive - Cloud Storage Application

MyDrive is a cloud storage application that provides geographically distributed file storage using Django, MinIO, and Nginx.

## Setup Instructions

### Set Environment
```bash
python3 -m venv env
source env/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
# or
pip install django
```

### Database Setup (PostgreSQL)
```bash
brew update
brew install postgresql
brew services start postgresql

# Create database and user
CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'root';
CREATE DATABASE DRIVE OWNER postgres;
```

### Run Database Migrations
```bash
python manage.py migrate
```

### Create Admin User
```bash
python manage.py createsuperuser
# Use username: root, password: root
# Enter 'yes' to bypass password validation
```

### Run Development Server
```bash
cd myproject
python manage.py runserver
```

## MinIO Setup

### Install MinIO
```bash
curl -O https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/
```

### Start Single MinIO Server
```bash
minio server --console-address ":9001" ~/minio-data --cache "C:\MinIO\cache"
```

### Start Multiple MinIO Servers (Distributed Mode)
```bash
minio server --console-address ":9001" --address ":9000" ~/minio-data-1 &
minio server --console-address ":9003" --address ":9002" ~/minio-data-2 &
minio server --console-address ":9005" --address ":9004" ~/minio-data-3 &
minio server --console-address ":9007" --address ":9006" ~/minio-data-4 &
```

### Distributed Storage Architecture

MinIO in this project is configured as a distributed object storage system rather than simply replicating data. The key features are:

1. **Distributed Storage**: The multiple MinIO nodes (4 per site) form a single logical storage pool, allowing the combined storage capacity of all nodes to be used efficiently.

2. **Erasure Coding**: MinIO uses erasure coding instead of simple replication:
   - Data is split into N/2 data parts and N/2 parity parts (where N is the total number of drives)
   - With 4 nodes, data is typically divided into 2 data shards and 2 parity shards
   - This approach provides redundancy while being more space-efficient than full replication
   - The system can tolerate the failure of up to half the nodes without losing data

3. **High Availability**: The distributed setup allows continued operation even if some nodes fail:
   - With 4 nodes, the system can continue functioning if up to 2 nodes fail
   - Data is automatically rebuilt when failed nodes come back online

4. **Consistent Hashing**: Requests for the same file are routed to the same node for operations like multipart uploads, ensuring consistency.

5. **Geographic Distribution**: The application uses two separate MinIO clusters (site1 and site2) for geographic redundancy, with requests routed based on the user's location using GeoIP.

### Configure MinIO Distributed Setup
```bash
# Set up aliases for each node
mc alias set node1 http://127.0.0.1:9000 minioadmin minioadmin
mc alias set node2 http://127.0.0.1:9002 minioadmin minioadmin
mc alias set node3 http://127.0.0.1:9004 minioadmin minioadmin
mc alias set node4 http://127.0.0.1:9006 minioadmin minioadmin

# Create buckets on each node
mc mb node1/mybucket
mc mb node2/mybucket
mc mb node3/mybucket
mc mb node4/mybucket

# Set up replication between nodes
mc admin relicate add node1 node2 node3 node4

# Check health of a node
mc admin info node1

# When a node goes down and comes back up, run:
mc admin replicate resync start
```

### Configure MinIO Notifications
```bash
mc admin config set node1 notify_webhook:bucket-events endpoint=http://127.0.0.1:9002 &
mc admin config set node1 notify_webhook:bucket-events endpoint=http://127.0.0.1:9004 &
mc admin config set node1 notify_webhook:bucket-events endpoint=http://127.0.0.1:9006 &
mc admin config set node2 notify_webhook:bucket-events endpoint=http://127.0.0.1:9000 &
mc admin config set node2 notify_webhook:bucket-events endpoint=http://127.0.0.1:9004 &
mc admin config set node2 notify_webhook:bucket-events endpoint=http://127.0.0.1:9006 &
mc admin config set node3 notify_webhook:bucket-events endpoint=http://127.0.0.1:9000 &
mc admin config set node3 notify_webhook:bucket-events endpoint=http://127.0.0.1:9002 &
mc admin config set node3 notify_webhook:bucket-events endpoint=http://127.0.0.1:9006 &
mc admin config set node4 notify_webhook:bucket-events endpoint=http://127.0.0.1:9000 &
mc admin config set node4 notify_webhook:bucket-events endpoint=http://127.0.0.1:9002 &
mc admin config set node4 notify_webhook:bucket-events endpoint=http://127.0.0.1:9004 

# Restart all nodes to apply changes
mc admin service restart node1 &&
mc admin service restart node2 &&
mc admin service restart node3 &&
mc admin service restart node4
```

## Docker Deployment

The application can be deployed using Docker Compose with the following components:

1. **Django Application** - Two instances for geographic distribution
   - Located in `deployment/django-app/`
   - Run with: `cd deployment/django-app && docker compose up -d`

2. **PostgreSQL Database**
   - Located in `deployment/postgres/`
   - Run with: `cd deployment/postgres && docker compose up -d`

3. **MinIO Object Storage**
   - Two clusters (site1 and site2) with 4 nodes each for distributed storage
   - Located in `deployment/site1/` and `deployment/site2/`
   - Run with: 
     ```bash
     cd deployment/site1 && docker compose up -d
     cd deployment/site2 && docker compose up -d
     ```

4. **Nginx Load Balancer**
   - Provides GeoIP-based routing between sites
   - Located in `deployment/nginx/`
   - Run with: `cd deployment/nginx && docker compose up -d`



## Domain Configuration

When using a custom domain (e.g., drive.aqlio.com), make sure to:

1. Add the domain to `ALLOWED_HOSTS` in Django settings
2. Add the domain to `CSRF_TRUSTED_ORIGINS` in Django settings
3. Update the MinIO external endpoint in the environment variables

## Troubleshooting Shared Files

If you're experiencing issues with shared files not appearing in the "Shared with me" section, you can use the following management commands:

### Check Shared Links
```bash
python myproject/manage.py check_shared_links
```

### Fix Shared Links
```bash
python myproject/manage.py fix_shared_links
```

# Run Project
source env/bin/activate
cd myproject
python manage.py runserver

# Run nginx