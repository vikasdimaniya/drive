cd site1
docker compose up -d
cd site2
docker compose up -d


mc replicate add site1/drive --remote-bucket 'https://admin:admin123@localhost:9010/drive' --replicate "delete,delete-marker,existing-objects"