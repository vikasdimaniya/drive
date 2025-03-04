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

@login_required
def list_user_files(request):
    """List all files uploaded by the logged-in user (without pre-signed URLs)"""
    user_id = request.user.id
    prefix = f"{user_id}/"

    response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix)

    files = []
    for obj in response.get("Contents", []):
        file_key = obj["Key"]
        files.append({"name": file_key.replace(prefix, ""), "key": file_key})

    return JsonResponse({"files": files})

@login_required
def get_presigned_url(request):
    """Generate a pre-signed URL for downloading a user's file"""
    data = json.loads(request.body)
    file_key = data.get("file_key")

    if not file_key:
        return JsonResponse({"error": "Missing file key"}, status=400)

    # Ensure the user is accessing only their own files
    user_id = request.user.id
    if not file_key.startswith(f"{user_id}/"):
        return JsonResponse({"error": "Unauthorized access"}, status=403)

    # Generate pre-signed URL
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": file_key},
        ExpiresIn=3600,  # 1-hour expiration
    )

    return JsonResponse({"presigned_url": presigned_url})

@login_required
def delete_user_file(request):
    """Delete a specific file uploaded by the user"""
    data = json.loads(request.body)
    file_key = data.get("file_key")

    if not file_key:
        return JsonResponse({"error": "File key is required"}, status=400)

    user_id = request.user.id
    if not file_key.startswith(f"{user_id}/"):
        return JsonResponse({"error": "Unauthorized access"}, status=403)

    try:
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_key,
        )
        return JsonResponse({"message": "File deleted successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
