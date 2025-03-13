# SETUP
SET ENVIRONMENT>   
python3 -m venv env   
source env/bin/activate   
   
INSTALL DEPENDENCIES>   
pip install -r requirements.txt   
or   
pip install django   
   
Run DB Migrations>   
python manage.py migrate   
   
Create Super User>   
python manage.py createsuperuser   
root   
root  
bypass yes     
   
RUN SERVER>   
cd dfs   
python manage.py runserver   

minio setup:
curl -O https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

minio start:
minio server --console-address ":9001" ~/minio-data

minio start multiple servers:
minio server --console-address ":9001" --address ":9000" ~/minio-data-1 &
minio server --console-address ":9003" --address ":9002" ~/minio-data-2 &
minio server --console-address ":9005" --address ":9004" ~/minio-data-3 &
minio server --console-address ":9007" --address ":9006" ~/minio-data-4
postgres setup:   
brew update   
brew install postgresql   
brew services start postgresql   

CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'root';
CREATE DATABASE DRIVE OWNER postgres;

SETUP django admin user: use username as root and password as root, you will have to enter password twice
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Run Project
source env/bin/activate
cd myproject
python manage.py runserver



setup multi minio server:
minio server --console-address ":9001" --address ":9000" ~/minio-data-1 &
minio server --console-address ":9003" --address ":9002" ~/minio-data-2 &
minio server --console-address ":9005" --address ":9004" ~/minio-data-3 &
minio server --console-address ":9007" --address ":9006" ~/minio-data-4 &


mc alias set node1 http://127.0.0.1:9000 minioadmin minioadmin
mc alias set node2 http://127.0.0.1:9002 minioadmin minioadmin
mc alias set node3 http://127.0.0.1:9004 minioadmin minioadmin
mc alias set node4 http://127.0.0.1:9006 minioadmin minioadmin

mc mb node1/mybucket
mc mb node2/mybucket
mc mb node3/mybucket
mc mb node4/mybucket

mc admin relicate add node1 node2 node3 node4

check health of a node:
mc admin info node1


when a node goes down, and comes back up we have to run:
mc admin replicate resync start



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

mc admin service restart node1 &&
mc admin service restart node2 &&
mc admin service restart node3 &&
mc admin service restart node4

# Troubleshooting Shared Files

If you're experiencing issues with shared files not appearing in the "Shared with me" section, you can use the following management commands to diagnose and fix the problem:

## Check Shared Links

This command displays all shared links in the database and their status:

```
python myproject/manage.py check_shared_links
```

## Fix Shared Links

This command finds shared links that are not properly associated with user accounts and fixes them:

```
python myproject/manage.py fix_shared_links
```

# Run Project
source env/bin/activate
cd myproject
python manage.py runserver
