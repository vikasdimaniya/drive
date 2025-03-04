import boto3
import json
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Initializing MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

@login_required
def dashboard(request):
    return render(request, 'myapp/dashboard.html')

# Multipart upload routes
@login_required
def create_multipart_upload(request):
    """Start a multipart upload and return an upload ID"""
    data = json.loads(request.body)
    file_name = data.get("file_name")

    if not file_name:
        return JsonResponse({"error": "File name is required"}, status=400)

    user_id = request.user.id

    # Store the file under the user's folder
    object_key = f"/{user_id}/{file_name}"

    response = s3_client.create_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=object_key,
    )

    return JsonResponse({"upload_id": response["UploadId"], "object_key": object_key})

@login_required
def get_part_presigned_url(request):
    """Generate signed URL for a single chunk"""
    data = json.loads(request.body)
    object_key = data.get("object_key")  # Now we use the correct folder path
    upload_id = data.get("upload_id")
    part_number = int(data.get("part_number"))

    if not object_key or not upload_id:
        return JsonResponse({"error": "Missing object key or upload ID"}, status=400)

    presigned_url = s3_client.generate_presigned_url(
        'upload_part',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': object_key,
            'UploadId': upload_id,
            'PartNumber': part_number
        },
        ExpiresIn=3600,
    )
    return JsonResponse({"presigned_url": presigned_url})

@login_required
def complete_multipart_upload(request):
    """Finalize multipart upload"""
    data = json.loads(request.body)
    file_name = data["object_key"]
    upload_id = data["upload_id"]
    parts = data["parts"]

    response = s3_client.complete_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )
    return JsonResponse({"message": "Upload completed", "location": response["Location"]})