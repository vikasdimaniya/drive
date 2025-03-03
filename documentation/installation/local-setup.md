
# One time configuration for standalone minio server on mac:   
mac:
curl -O https://dl.min.io/server/minio/release/darwin-arm64/minio   
chmod +x minio   
sudo mv minio /usr/local/bin/   
minio --version   
minio server --console-address ":9001" ~/minio-data   
   
Go to http://localhost:9001/   
enter the access key and secret key   


brew install minio/stable/mc   
mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin
mc mb myminio/mybucket

# Testing miniO using terminal:
mc cp ~/Downloads/testfile.txt myminio/mybucket/
mc ls myminio/mybucket/
mc cp myminio/mybucket/testfile.txt ~/Downloads/


## Create a signed URL:
One time steps:
mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin
mc anonymous set public myminio/mybucket

To generate just a single singed URL, repeate to generate more unique URLs:
mc share download myminio/mybucket/testfile.txt

Open browser and paste the URL to download the file.

## Test large file upload using aws-cli:
### Install and configure aws-cli:
brew install awscli
aws --version
aws configure set aws_access_key_id minioadmin
aws configure set aws_secret_access_key minioadmin
aws configure set default.region us-east-1
aws configure set default.s3.endpoint http://127.0.0.1:9000
aws configure set default.s3.signature_version s3v4
### Test large file upload:
export AWS_MAX_ATTEMPTS=5
export AWS_S3_MULTIPART_THRESHOLD=104857600  # 100MB
export AWS_S3_MULTIPART_CHUNKSIZE=524288000  # 512MB

aws s3 cp ~/Downloads/docker.dm s3://mybucket/ --endpoint-url http://127.0.0.1:9000

## Test large file using minio client:
mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin
mc cp --multipart-chunk-size 512MiB ~/Downloads/docker.dmg myminio/mybucket/

You can run the command to see in how many chunks the file is uploaded by running the following command and see the output ETag: 17b9101baa84c991d390a8ba85e9bf54-725, here 725 signifies the number of chunks.
mc stat myminio/mybucket/10gb-file.zip


