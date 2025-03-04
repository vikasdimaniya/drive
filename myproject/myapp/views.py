import boto3
import json
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, 'myapp/dashboard.html')

# Initializing MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


# Multipart upload routes
def create_multipart_upload(request):
    """Start a multipart upload and return an upload ID"""
    data = json.loads(request.body)
    file_name = data.get("file_name")

    response = s3_client.create_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
    )
    return JsonResponse({"upload_id": response["UploadId"]})


def get_part_presigned_url(request):
    """Generate signed URL for a single chunk"""
    data = json.loads(request.body)
    file_name = data["file_name"]
    upload_id = data["upload_id"]
    part_number = int(data["part_number"])

    presigned_url = s3_client.generate_presigned_url(
        'upload_part',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_name,
            'UploadId': upload_id,
            'PartNumber': part_number
        },
        ExpiresIn=3600,
    )
    return JsonResponse({"presigned_url": presigned_url})


def complete_multipart_upload(request):
    """Finalize multipart upload"""
    data = json.loads(request.body)
    file_name = data["file_name"]
    upload_id = data["upload_id"]
    parts = data["parts"]

    response = s3_client.complete_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )
    return JsonResponse({"message": "Upload completed", "location": response["Location"]})