import boto3
import json
import logging
import os
import uuid
import re
import traceback
import platform
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from myapp.models import FileMetadata, SharedLink
from .forms import SignupForm
from django.utils import timezone
import subprocess
import threading
import tempfile
import traceback

# Initializing MinIO client for internal operations
s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

# Initializing MinIO client for generating presigned URLs (using external endpoint)
s3_external_client = boto3.client(
    's3',
    endpoint_url=getattr(settings, 'AWS_S3_EXTERNAL_ENDPOINT', settings.AWS_S3_ENDPOINT_URL),
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

logger = logging.getLogger(__name__)

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
    # Associate any shared files with the current user
    associate_shared_files_with_user(request.user)
    return render(request, 'myapp/dashboard.html')

@login_required
def refresh_shared_files(request):
    """Manually refresh the association of shared files with the current user"""
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)
    
    # Associate shared files with the current user
    count = associate_shared_files_with_user(request.user)
    
    return JsonResponse({
        "message": "Shared files refreshed successfully",
        "associated_files": count
    })

def associate_shared_files_with_user(user):
    """Associate any shared files with the user's account based on email"""
    if not user.email and not user.username:
        return 0
    
    # Find shared links that match the user's email OR username but aren't associated with the user
    # Also exclude files that have been removed by the recipient
    query = Q()
    if user.email:
        query |= Q(shared_with_email=user.email)
    
    # Also try with username as email (for users without explicit email set)
    query |= Q(shared_with_email=user.username)
    
    shared_links = SharedLink.objects.filter(
        query,
        shared_with__isnull=True,
        is_active=True,
        removed_by_recipient=False
    )
    
    # Log the number of links found
    count = shared_links.count()
    print(f"Found {count} unassociated shared links for user {user.username} with email {user.email}")
    
    # Associate each link with the user
    for link in shared_links:
        link.shared_with = user
        link.save()
        print(f"Associated shared file '{link.file.file_name}' with user {user.username}")
    
    return count

# Multipart upload routes
@login_required
def create_multipart_upload(request):
    """Start a multipart upload and return an upload ID"""
    data = json.loads(request.body)
    file_name = data.get("file_name")

    if not file_name:
        return JsonResponse({"error": "File name is required"}, status=400)

    user_id = request.user.id

    # Store the file under the user's folder - remove leading slash to prevent double slash
    object_key = f"{user_id}/{file_name}"

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

    # Use the external client for presigned URLs
    presigned_url = s3_external_client.generate_presigned_url(
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
    logger = logging.getLogger('myapp')
    
    try:
        data = json.loads(request.body)
        logger.debug(f"Received multipart complete request: {data}")
        
        file_name = data["object_key"]
        upload_id = data["upload_id"]
        parts = data["parts"]
        
        logger.info(f"Completing multipart upload for file: {file_name}, upload_id: {upload_id}, parts count: {len(parts)}")
        
        try:
            response = s3_client.complete_multipart_upload(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_name,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            logger.info(f"S3 complete_multipart_upload response: {response}")
        except Exception as e:
            logger.error(f"S3 complete_multipart_upload failed: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"S3 multipart completion failed: {str(e)}"}, status=500)

        # Fetch file metadata from S3
        try:
            head_object = s3_client.head_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_name
            )
            file_size = head_object["ContentLength"]
            file_type = head_object["ContentType"]
            logger.info(f"Retrieved file metadata: size={file_size}, type={file_type}")
        except Exception as e:
            logger.error(f"Failed to get file metadata: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"Failed to get file metadata: {str(e)}"}, status=500)

        # Store metadata in the database - check if file already exists
        try:
            # Extract the actual filename from the path
            actual_filename = file_name.split("/")[-1]
            file_path = f"{request.user.id}/{actual_filename}"
            
            # Check if file already exists
            existing_file, created = FileMetadata.objects.get_or_create(
                file_path=file_path,
                defaults={
                    "user": request.user,
                    "file_name": actual_filename,
                    "file_size": file_size,
                    "file_type": file_type,
                }
            )
            
            if not created:
                # Update the existing file metadata
                existing_file.file_size = file_size
                existing_file.file_type = file_type
                existing_file.last_modified = timezone.now()
                existing_file.save()
                logger.info(f"Updated existing file metadata for {file_name}")
            else:
                logger.info(f"Created new file metadata for {file_name}")
                
        except Exception as e:
            logger.error(f"Metadata storage failed: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"Metadata storage failed: {str(e)}"}, status=500)

        return JsonResponse({"message": "Upload completed", "location": response["Location"]})
    except KeyError as e:
        logger.error(f"Missing required field in request: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Missing required field: {str(e)}"}, status=400)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in complete_multipart_upload: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

@login_required
def list_user_files(request):
    """List all files uploaded by the logged-in user with pagination and sorting"""
    # Get pagination parameters
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    
    # Get sorting parameters
    sort_by = request.GET.get('sort_by', 'upload_date')  # Default sort by upload date
    sort_order = request.GET.get('sort_order', 'desc')  # Default newest first
    
    # Map sort_by parameter to model field
    sort_field_map = {
        'name': 'file_name',
        'size': 'file_size',
        'date': 'upload_date',
        'type': 'file_type',
        'upload_date': 'upload_date'
    }
    
    sort_field = sort_field_map.get(sort_by, 'upload_date')
    
    # Apply sort direction
    if sort_order.lower() == 'asc':
        order_by = sort_field
    else:
        order_by = f'-{sort_field}'
    
    # Query database for files - exclude trashed files
    user_files = FileMetadata.objects.filter(user=request.user, trashed=False).order_by(order_by)
    
    # Create paginator
    paginator = Paginator(user_files, page_size)
    
    try:
        files_page = paginator.page(page)
    except PageNotAnInteger:
        files_page = paginator.page(1)
    except EmptyPage:
        files_page = paginator.page(paginator.num_pages)
    
    # Format response
    files = []
    for file in files_page:
        files.append({
            "name": file.file_name,
            "key": file.file_path,
            "size": file.file_size,
            "type": file.file_type,
            "upload_date": file.upload_date.isoformat(),
            "last_modified": file.last_modified.isoformat()
        })
    
    return JsonResponse({
        "files": files,
        "pagination": {
            "total": paginator.count,
            "page": files_page.number,
            "page_size": page_size,
            "num_pages": paginator.num_pages,
            "has_next": files_page.has_next(),
            "has_previous": files_page.has_previous()
        }
    })

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

    # Use the external client for presigned URLs
    presigned_url = s3_external_client.generate_presigned_url(
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
    """Search for a file uploaded by the logged-in user with pagination and sorting"""
    query = request.GET.get("query", "").lower().strip()

    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)
    
    # Get pagination parameters
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    
    # Get sorting parameters
    sort_by = request.GET.get('sort_by', 'upload_date')  # Default sort by upload date
    sort_order = request.GET.get('sort_order', 'desc')  # Default newest first
    
    # Map sort_by parameter to model field
    sort_field_map = {
        'name': 'file_name',
        'size': 'file_size',
        'date': 'upload_date',
        'type': 'file_type',
        'upload_date': 'upload_date'
    }
    
    sort_field = sort_field_map.get(sort_by, 'upload_date')
    
    # Apply sort direction
    if sort_order.lower() == 'asc':
        order_by = sort_field
    else:
        order_by = f'-{sort_field}'
    
    # Query database for files - exclude trashed files
    user_files = FileMetadata.objects.filter(
        user=request.user, 
        file_name__icontains=query,
        trashed=False
    ).order_by(order_by)
    
    # Create paginator
    paginator = Paginator(user_files, page_size)
    
    try:
        files_page = paginator.page(page)
    except PageNotAnInteger:
        files_page = paginator.page(1)
    except EmptyPage:
        files_page = paginator.page(paginator.num_pages)
    
    # Format response
    files = []
    for file in files_page:
        files.append({
            "name": file.file_name,
            "key": file.file_path,
            "size": file.file_size,
            "type": file.file_type,
            "upload_date": file.upload_date.isoformat(),
            "last_modified": file.last_modified.isoformat()
        })
    
    return JsonResponse({
        "files": files,
        "pagination": {
            "total": paginator.count,
            "page": files_page.number,
            "page_size": page_size,
            "num_pages": paginator.num_pages,
            "has_next": files_page.has_next(),
            "has_previous": files_page.has_previous()
        }
    })

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
        # Try to find user by email first
        recipient_user = User.objects.get(email=recipient_email)
        print(f"Found recipient user by email: {recipient_user.username}")
    except User.DoesNotExist:
        try:
            # If not found by email, try by username
            recipient_user = User.objects.get(username=recipient_email)
            print(f"Found recipient user by username: {recipient_user.username}")
        except User.DoesNotExist:
            # If not a registered user, we'll just store their email
            print(f"Recipient user not found for email/username: {recipient_email}")
            pass
    
    # Check if the file is already shared with this recipient
    existing_share = SharedLink.objects.filter(
        file=file_metadata,
        owner=request.user,
        is_active=True,
    )
    
    # Check by user if recipient_user exists, otherwise check by email
    if recipient_user:
        existing_share = existing_share.filter(shared_with=recipient_user)
    else:
        existing_share = existing_share.filter(shared_with_email=recipient_email)
    
    if existing_share.exists():
        # File is already shared with this recipient
        existing_link = existing_share.first()
        share_url = f"{request.scheme}://{request.get_host()}/shared/{existing_link.token}"
        
        return JsonResponse({
            "error": "This file is already shared with this recipient",
            "share_url": share_url,
            "expires_at": existing_link.expires_at.isoformat() if existing_link.expires_at else None,
            "token": str(existing_link.token),
            "recipient": recipient_user.username if recipient_user else recipient_email,
            "already_shared": True
        }, status=409)  # 409 Conflict
    
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
        
        # Generate a pre-signed URL for the file using the external client
        presigned_url = s3_external_client.generate_presigned_url(
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
    # Get the current user's email
    user_email = request.user.email or request.user.username
    
    # Log debugging information
    print(f"Searching for files shared with user: {request.user.username}, email: {user_email}")
    
    # Get files shared directly with the user (by user ID or email)
    # Exclude files that have been removed by the recipient
    shared_links = SharedLink.objects.filter(
        (Q(shared_with=request.user) | Q(shared_with_email=user_email)),
        is_active=True,
        removed_by_recipient=False
    ).select_related('file', 'owner')
    
    # Log the number of shared links found
    print(f"Found {shared_links.count()} shared links for user {request.user.username}")
    
    files = []
    for link in shared_links:
        # Check if the link is valid (not expired)
        if link.is_valid:
            # Log each valid shared link
            print(f"Valid shared link: {link.file.file_name} shared by {link.owner.username}")
            
            files.append({
                "name": link.file.file_name,
                "key": link.file.file_path,
                "shared_by": link.owner.username,
                "shared_date": link.created_at.isoformat(),
                "expires_at": link.expires_at.isoformat() if link.expires_at else None,
                "token": str(link.token)
            })
        else:
            # Log invalid links for debugging
            print(f"Invalid shared link: {link.file.file_name} (expired or inactive)")
    
    # Return the list of files
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
        # Log the revoke request
        print(f"Revoking access for token: {token}, requested by user: {request.user.username}")
        
        shared_link = SharedLink.objects.get(token=token, owner=request.user)
        
        # Log the shared link details
        print(f"Found shared link: {shared_link.file.file_name}, shared with: {shared_link.shared_with.username if shared_link.shared_with else shared_link.shared_with_email}")
        
        shared_link.is_active = False
        shared_link.save()
        
        # Log the successful revocation
        print(f"Successfully revoked access for token: {token}")
        
        return JsonResponse({
            "message": "Access revoked successfully",
            "file_name": shared_link.file.file_name,
            "shared_with": shared_link.shared_with.username if shared_link.shared_with else shared_link.shared_with_email
        })
    except SharedLink.DoesNotExist:
        # Log the error
        print(f"Shared link not found for token: {token}, requested by user: {request.user.username}")
        
        return JsonResponse({"error": "Shared link not found or you don't have permission"}, status=404)

@login_required
def remove_shared_with_me(request):
    """Remove a file that has been shared with the current user"""
    data = json.loads(request.body)
    token = data.get("token")
    
    if not token:
        return JsonResponse({"error": "Token is required"}, status=400)
    
    try:
        # Find the shared link where the current user is the recipient
        # We need to check both shared_with and shared_with_email fields
        user_email = request.user.email or request.user.username
        
        # First try to find by direct user association
        try:
            shared_link = SharedLink.objects.get(
                token=token, 
                shared_with=request.user,
                is_active=True
            )
        except SharedLink.DoesNotExist:
            # If not found, try by email
            shared_link = SharedLink.objects.get(
                token=token, 
                shared_with_email=user_email,
                is_active=True
            )
        
        # Log the removal for debugging
        print(f"Removing shared file '{shared_link.file.file_name}' from user {request.user.username}")
        
        # Instead of deleting the link, we'll just remove the association with the current user
        # This way, the owner still sees that they've shared the file, but the recipient won't see it anymore
        shared_link.shared_with = None
        
        # Also add a flag to indicate this user has removed it
        # We'll need to add this field to the model
        shared_link.removed_by_recipient = True
        shared_link.save()
        
        return JsonResponse({"message": "File removed from your shared files"})
    except SharedLink.DoesNotExist:
        return JsonResponse({"error": "Shared link not found or you don't have permission"}, status=404)

@login_required
def move_to_trash(request):
    """
    Move a file to trash.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        file_key = data.get('file_key')
        
        if not file_key:
            return JsonResponse({'error': 'File key is required'}, status=400)
        
        # Get the file metadata
        file = FileMetadata.objects.get(user=request.user, file_path=file_key)
        
        # Mark as trashed and set trash date
        file.trashed = True
        file.trash_date = timezone.now()
        file.save()
        
        logger.info(f"File moved to trash: {file_key} by user {request.user.username}")
        
        return JsonResponse({'message': f"File '{file.file_name}' moved to trash"})
    except FileMetadata.DoesNotExist:
        logger.error(f"File not found for trash: {file_key}")
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        logger.error(f"Error moving file to trash: {str(e)}")
        return JsonResponse({'error': 'Failed to move file to trash'}, status=500)

@login_required
def restore_from_trash(request):
    """
    Restore a file from trash.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        file_key = data.get('file_key')
        
        if not file_key:
            return JsonResponse({'error': 'File key is required'}, status=400)
        
        # Get the file metadata
        file = FileMetadata.objects.get(user=request.user, file_path=file_key, trashed=True)
        
        # Restore from trash
        file.trashed = False
        file.trash_date = None
        file.save()
        
        logger.info(f"File restored from trash: {file_key} by user {request.user.username}")
        
        return JsonResponse({'message': f"File '{file.file_name}' restored from trash"})
    except FileMetadata.DoesNotExist:
        logger.error(f"File not found for restore: {file_key}")
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        logger.error(f"Error restoring file from trash: {str(e)}")
        return JsonResponse({'error': 'Failed to restore file from trash'}, status=500)

@login_required
def list_trash(request):
    """
    List all files in the user's trash.
    """
    try:
        # Get all trashed files for the current user
        trashed_files = FileMetadata.objects.filter(
            user=request.user,
            trashed=True
        ).order_by('-trash_date')
        
        # Calculate days remaining before permanent deletion
        files_data = []
        for file in trashed_files:
            # Calculate days remaining (30 days from trash_date)
            if file.trash_date:
                days_passed = (timezone.now() - file.trash_date).days
                days_remaining = max(0, 30 - days_passed)
            else:
                days_remaining = 30
            
            files_data.append({
                'name': file.file_name,
                'key': file.file_path,
                'size': file.file_size,
                'type': file.file_type,
                'upload_date': file.upload_date.isoformat() if file.upload_date else None,
                'last_modified': file.last_modified.isoformat() if file.last_modified else None,
                'trash_date': file.trash_date.isoformat() if file.trash_date else None,
                'days_remaining': days_remaining
            })
        
        return JsonResponse({'files': files_data})
    except Exception as e:
        logger.error(f"Error listing trash: {str(e)}")
        return JsonResponse({'error': 'Failed to list trash'}, status=500)

@login_required
def empty_trash(request):
    """
    Permanently delete all files in trash.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        # Get all trashed files for the current user
        trashed_files = FileMetadata.objects.filter(
            user=request.user,
            trashed=True
        )
        
        count = trashed_files.count()
        
        if count == 0:
            return JsonResponse({'message': 'Trash is already empty'})
        
        # Delete files from storage
        for file in trashed_files:
            try:
                # Delete from MinIO
                s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=file.file_path
                )
                logger.info(f"File deleted from storage: {file.file_path}")
            except Exception as e:
                logger.error(f"Error deleting file from storage: {file.file_path}, error: {str(e)}")
        
        # Delete metadata from database
        trashed_files.delete()
        
        logger.info(f"Trash emptied by user {request.user.username}, {count} files deleted")
        
        return JsonResponse({'message': f"Trash emptied. {count} files permanently deleted."})
    except Exception as e:
        logger.error(f"Error emptying trash: {str(e)}")
        return JsonResponse({'error': 'Failed to empty trash'}, status=500)

@login_required
def debug_shared_link(request, token):
    """
    Debug endpoint to check the status of a shared link.
    For development purposes only.
    """
    try:
        # Get the shared link
        shared_link = SharedLink.objects.get(token=token)
        
        # Format response data
        response_data = {
            'token': str(shared_link.token),
            'file_key': shared_link.file_key,
            'file_name': shared_link.file_name,
            'owner': shared_link.owner.username,
            'created_at': shared_link.created_at.isoformat(),
            'expires_at': shared_link.expires_at.isoformat() if shared_link.expires_at else None,
            'is_active': shared_link.is_active,
            'shared_with': shared_link.shared_with.username if shared_link.shared_with else None
        }
        
        logger.info(f"Debug shared link: {token} by user {request.user.username}")
        
        return JsonResponse(response_data)
    except SharedLink.DoesNotExist:
        logger.error(f"Shared link not found for debug: {token}")
        return JsonResponse({'error': 'Shared link not found'}, status=404)
    except Exception as e:
        logger.error(f"Error debugging shared link: {str(e)}")
        return JsonResponse({'error': 'Failed to debug shared link'}, status=500)

@staff_member_required
def monitoring_dashboard(request):
    """Monitoring dashboard for admin users to view MinIO server information"""
    logger.info("Accessing monitoring dashboard")
    return render(request, 'myapp/monitoring.html')

@staff_member_required
def get_minio_info(request, site):
    """API endpoint to get MinIO server information for a specific site"""
    logger.info(f"Getting MinIO info for site {site}")
    site_name = f"site{site}"
    
    if not re.match(r'^site[12]$', site_name):
        logger.error(f"Invalid site name: {site_name}")
        return JsonResponse({"error": "Invalid site name"}, status=400)
    
    try:
        # Create a temp directory for mc config
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temp directory for mc config: {temp_dir}")
        os.environ["MC_CONFIG_DIR"] = temp_dir
        
        # Set alias for the site
        if site_name == "site1":
            endpoint = os.environ.get('SITE1_MINIO_ENDPOINT', 'localhost:9000')
        else:
            endpoint = os.environ.get('SITE2_MINIO_ENDPOINT', 'localhost:9000')
            
        access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'admin')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'admin123')
        
        logger.debug(f"Setting up mc alias for {site_name} with endpoint {endpoint}")
        
        # Check if mc exists
        mc_path = "mc"
        if os.name == 'nt':  # Windows
            mc_path = os.path.join(os.getcwd(), "mc.exe")
        elif os.path.exists(os.path.join(os.getcwd(), "mc")):
            mc_path = os.path.join(os.getcwd(), "mc")
            
        logger.debug(f"Using mc path: {mc_path}")
            
        # Create alias
        try:
            alias_result = subprocess.run(
                [mc_path, "alias", "set", site_name, f"http://{endpoint}", access_key, secret_key],
                check=True,
                capture_output=True,
                text=True
            )
            logger.debug(f"Alias result: {alias_result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting alias: {e.stderr}")
            return JsonResponse({
                "error": f"Error setting MinIO alias: {e.stderr}",
                "command": f"mc alias set {site_name} http://{endpoint} [access_key] [secret_key]"
            }, status=500)
        
        # For development, we'll simulate the response if we can't connect to the MinIO server
        if settings.DEBUG:
            try:
                # First try to get actual data
                info_result = subprocess.run(
                    [mc_path, "admin", "info", "--json", site_name],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=3  # Add a timeout for development
                )
                info = json.loads(info_result.stdout)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
                # If it fails, return mock data
                logger.warning(f"Returning mock data for {site_name} in development mode")
                return JsonResponse({
                    "info": {
                        "servers": [
                            {"endpoint": f"{site_name}-minio1-1:9000", "state": "online", "uptime": 3600, "version": "RELEASE.2024-01-16T16-07-38Z", "drives": [{"usedspace": 1000000, "totalspace": 10000000}]},
                            {"endpoint": f"{site_name}-minio1-2:9000", "state": "online", "uptime": 3600, "version": "RELEASE.2024-01-16T16-07-38Z", "drives": [{"usedspace": 2000000, "totalspace": 10000000}]}
                        ],
                        "buckets": {"count": 5},
                        "objects": {"count": 1024},
                        "usage": {"size": 3000000},
                        "backend": {"backendType": "Erasure", "onlineDisks": 4, "standardSCParity": 2}
                    },
                    "user_count": 42
                })
        
        # Get server info
        try:
            info_result = subprocess.run(
                [mc_path, "admin", "info", "--json", site_name],
                check=True,
                capture_output=True,
                text=True
            )
            logger.debug(f"Info command output: {info_result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting server info: {e.stderr}")
            return JsonResponse({
                "error": f"Error getting MinIO server info: {e.stderr}",
                "command": f"mc admin info --json {site_name}"
            }, status=500)
        
        # Get user folders info
        try:
            ls_result = subprocess.run(
                [mc_path, "ls", f"{site_name}/drive", "--json"],
                check=True,
                capture_output=True,
                text=True
            )
            logger.debug(f"LS command executed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error listing folders: {e.stderr}")
            # Continue with partial data, just set folder count to 0
            ls_result = None
        
        # Parse the output to extract folder count
        folder_count = 0
        if ls_result:
            for line in ls_result.stdout.strip().split('\n'):
                if line:
                    try:
                        entry = json.loads(line)
                        if entry.get('type') == 'folder':
                            folder_count += 1
                    except json.JSONDecodeError:
                        pass
        
        # Clean up temp dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Parse server info
        try:
            info = json.loads(info_result.stdout)
            info['user_count'] = folder_count
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing server info JSON: {e}")
            return JsonResponse({"error": f"Error parsing server info: {str(e)}"}, status=500)
        
        return JsonResponse(info)
    except Exception as e:
        logger.exception(f"Unexpected error in get_minio_info: {str(e)}")
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

@staff_member_required
def get_folder_count(request, site):
    """API endpoint to get count of user folders in the drive bucket"""
    logger.info(f"Getting folder count for site {site}")
    site_name = f"site{site}"
    
    if not re.match(r'^site[12]$', site_name):
        return JsonResponse({"error": "Invalid site name"}, status=400)
    
    # For development, return mock data if DEBUG is True
    if settings.DEBUG:
        logger.warning(f"Returning mock folder count data for {site_name} in development mode")
        return JsonResponse({
            "count": 42,
            "folders": [
                {"name": "user1", "size": 5242880, "type": "folder"},
                {"name": "user2", "size": 3145728, "type": "folder"},
                {"name": "user3", "size": 10485760, "type": "folder"}
            ]
        })
    
    try:
        # Create a temp directory for mc config
        temp_dir = tempfile.mkdtemp()
        os.environ["MC_CONFIG_DIR"] = temp_dir
        
        # Set alias for the site
        if site_name == "site1":
            endpoint = os.environ.get('SITE1_MINIO_ENDPOINT', 'site1-minio1-1:9000')
        else:
            endpoint = os.environ.get('SITE2_MINIO_ENDPOINT', 'site2-minio1-1:9000')
            
        access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'admin')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'admin123')
        
        # Check if mc exists
        mc_path = "mc"
        if os.name == 'nt':  # Windows
            mc_path = os.path.join(os.getcwd(), "mc.exe")
        elif os.path.exists(os.path.join(os.getcwd(), "mc")):
            mc_path = os.path.join(os.getcwd(), "mc")
        
        # Create alias
        subprocess.run(
            [mc_path, "alias", "set", site_name, f"http://{endpoint}", access_key, secret_key],
            check=True,
            capture_output=True
        )
        
        # Get folders in drive bucket
        result = subprocess.run(
            [mc_path, "ls", f"{site_name}/drive", "--json"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Parse the output to extract folder count
        folders = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    entry = json.loads(line)
                    if entry.get('type') == 'folder':
                        folders.append(entry)
                except:
                    pass
        
        # Clean up temp dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return JsonResponse({"count": len(folders), "folders": folders})
    except subprocess.CalledProcessError as e:
        error_message = f"Error executing MinIO command: {e.stderr}"
        logger.error(error_message)
        return JsonResponse({"error": error_message}, status=500)
    except Exception as e:
        logger.exception(f"Unexpected error in get_folder_count: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

def check_mc_installed(request):
    """Check if MinIO client (mc) is installed and download if needed"""
    logger.info("Checking if MinIO client is installed")
    try:
        # Check if mc is already downloaded
        mc_path = None
        if os.name == 'nt':  # Windows
            mc_path = os.path.join(os.getcwd(), "mc.exe")
        else:
            mc_path = os.path.join(os.getcwd(), "mc")
            
        if os.path.exists(mc_path):
            logger.info(f"MinIO client already exists at {mc_path}")
            if os.name == 'posix':
                os.chmod(mc_path, 0o755)  # Make executable on Unix systems
            return JsonResponse({"status": "installed", "path": mc_path})
        
        # If we're here, we need to download the client
        logger.info("Downloading MinIO client...")
        
        # Determine platform and URL
        if os.name == 'posix':
            # Linux or macOS
            if platform.system() == 'Darwin':
                # macOS
                url = "https://dl.min.io/client/mc/release/darwin-amd64/mc"
            else:
                # Linux
                url = "https://dl.min.io/client/mc/release/linux-amd64/mc"
            download_path = mc_path
        else:
            # Windows
            url = "https://dl.min.io/client/mc/release/windows-amd64/mc.exe"
            download_path = mc_path
        
        logger.info(f"Downloading from {url} to {download_path}")
        
        # Use requests instead of subprocess for better cross-platform compatibility
        import requests
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Make executable on Unix systems
        if os.name == 'posix':
            os.chmod(download_path, 0o755)
            
        logger.info(f"MinIO client downloaded successfully to {download_path}")
        return JsonResponse({"status": "installed", "path": download_path})
    except Exception as e:
        logger.exception(f"Error checking/installing mc: {str(e)}")
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


