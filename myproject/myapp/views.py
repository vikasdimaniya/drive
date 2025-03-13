import boto3
import json
import uuid
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from myapp.models import FileMetadata, SharedLink
from .forms import SignupForm

# Initializing MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

def home(request):
    """Redirect to login page from root URL"""
    return redirect('login')

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'myapp/signup.html', {'form': form})

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

    # Fetch file metadata from S3
    head_object = s3_client.head_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_name
    )
    file_size = head_object["ContentLength"]
    file_type = head_object["ContentType"]

    # Store metadata in the database
    try:
        FileMetadata.objects.create(
            user=request.user,
            file_name=file_name.split("/")[-1],
            file_path=f"{request.user.id}/{file_name.split('/')[-1]}",
            file_size=file_size,
            file_type=file_type,
        )
    except Exception as e:
        return JsonResponse({"error": f"Metadata storage failed: {str(e)}"}, status=500)

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

        # Delete metadata from the database
        existing_metadata = FileMetadata.objects.filter(user=request.user, file_path=file_key)
        if existing_metadata.exists():
            deleted_count, _ = existing_metadata.delete()

        return JsonResponse({"message": "File deleted successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def search_user_files(request):
    """Search for a file uploaded by the logged-in user"""
    query = request.GET.get("query", "").lower().strip()

    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)

    user_files = FileMetadata.objects.filter(user=request.user, file_name__icontains=query).values(
        "file_name", "file_path"
    )

    files = [{"name": file["file_name"], "key": file["file_path"]} for file in user_files]
    return JsonResponse({"files": files})

@login_required
def create_shared_link(request):
    """Create a shared link for a file with a specific user"""
    data = json.loads(request.body)
    file_key = data.get("file_key")
    recipient_email = data.get("recipient_email")
    expiry_days = data.get("expiry_days")
    
    if not file_key or not recipient_email:
        return JsonResponse({"error": "File key and recipient email are required"}, status=400)
    
    # Ensure the user is sharing only their own files
    user_id = request.user.id
    if not file_key.startswith(f"{user_id}/"):
        return JsonResponse({"error": "Unauthorized access"}, status=403)
    
    # Get the file metadata
    try:
        file_metadata = FileMetadata.objects.get(user=request.user, file_path=file_key)
    except FileMetadata.DoesNotExist:
        return JsonResponse({"error": "File not found"}, status=404)
    
    # Create expiration date if provided
    expires_at = None
    if expiry_days:
        expires_at = datetime.now() + timedelta(days=int(expiry_days))
    
    # Check if recipient is a registered user
    recipient_user = None
    try:
        recipient_user = User.objects.get(email=recipient_email)
    except User.DoesNotExist:
        # If not a registered user, we'll just store their email
        pass
    
    # Create a shared link
    shared_link = SharedLink.objects.create(
        file=file_metadata,
        owner=request.user,
        shared_with=recipient_user,
        shared_with_email=recipient_email,
        expires_at=expires_at
    )
    
    # Generate the full URL for the shared link
    share_url = f"{request.scheme}://{request.get_host()}/shared/{shared_link.token}"
    
    # Send email notification (this would be implemented with a proper email backend)
    try:
        send_mail(
            f'{request.user.username} shared a file with you',
            f'Hello,\n\n{request.user.username} has shared the file "{file_metadata.file_name}" with you.\n\nYou can access it using this link: {share_url}\n\nRegards,\nMyDrive Team',
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        shared_link.is_email_sent = True
        shared_link.save()
    except Exception as e:
        # Log the error but continue
        print(f"Error sending email: {str(e)}")
    
    return JsonResponse({
        "share_url": share_url,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "token": str(shared_link.token),
        "recipient": recipient_user.username if recipient_user else recipient_email
    })

def access_shared_file(request, token):
    """Access a file via a shared link"""
    try:
        # Find the shared link by token
        shared_link = get_object_or_404(SharedLink, token=token)
        
        # Check if the link is valid
        if not shared_link.is_valid:
            return render(request, 'myapp/shared_link_error.html', {
                'error': 'This link has expired or is no longer active.'
            })
        
        # Get the file metadata
        file_metadata = shared_link.file
        
        # Generate a pre-signed URL for the file
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME, 
                "Key": file_metadata.file_path
            },
            ExpiresIn=3600,  # 1-hour expiration
        )
        
        # If user is logged in and is the recipient, add to their shared files
        if request.user.is_authenticated:
            if shared_link.shared_with_email == request.user.email and not shared_link.shared_with:
                shared_link.shared_with = request.user
                shared_link.save()
        
        # Redirect to the pre-signed URL for direct download
        return redirect(presigned_url)
        
    except Http404:
        return render(request, 'myapp/shared_link_error.html', {
            'error': 'Invalid or expired link.'
        })

@login_required
def list_shared_with_me(request):
    """List all files shared with the logged-in user"""
    # Get files shared directly with the user
    shared_links = SharedLink.objects.filter(
        Q(shared_with=request.user) | Q(shared_with_email=request.user.email),
        is_active=True
    ).select_related('file', 'owner')
    
    files = []
    for link in shared_links:
        if link.is_valid:
            files.append({
                "name": link.file.file_name,
                "key": link.file.file_path,
                "shared_by": link.owner.username,
                "shared_date": link.created_at.isoformat(),
                "expires_at": link.expires_at.isoformat() if link.expires_at else None,
                "token": str(link.token)
            })
    
    return JsonResponse({"files": files})

@login_required
def list_shared_by_me(request):
    """List all files shared by the logged-in user"""
    shared_links = SharedLink.objects.filter(
        owner=request.user
    ).select_related('file', 'shared_with')
    
    files = []
    for link in shared_links:
        recipient = link.shared_with.username if link.shared_with else link.shared_with_email
        files.append({
            "name": link.file.file_name,
            "key": link.file.file_path,
            "shared_with": recipient,
            "shared_date": link.created_at.isoformat(),
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "is_active": link.is_active,
            "is_valid": link.is_valid,
            "token": str(link.token)
        })
    
    return JsonResponse({"files": files})

@login_required
def revoke_access(request):
    """Revoke access to a shared file"""
    data = json.loads(request.body)
    token = data.get("token")
    
    if not token:
        return JsonResponse({"error": "Token is required"}, status=400)
    
    try:
        shared_link = SharedLink.objects.get(token=token, owner=request.user)
        shared_link.is_active = False
        shared_link.save()
        return JsonResponse({"message": "Access revoked successfully"})
    except SharedLink.DoesNotExist:
        return JsonResponse({"error": "Shared link not found or you don't have permission"}, status=404)


