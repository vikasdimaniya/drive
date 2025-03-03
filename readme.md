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
