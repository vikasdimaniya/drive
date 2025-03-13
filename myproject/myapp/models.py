from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime, timedelta

class FileMetadata(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, db_index=True)  # Adding db_index for faster lookups
    file_path = models.CharField(max_length=1024, unique=True)  # MinIO object key
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    upload_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.file_name} ({self.user.username})"

class SharedLink(models.Model):
    file = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='shared_links')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_by_me')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_with_me', null=True, blank=True)
    shared_with_email = models.EmailField(null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_email_sent = models.BooleanField(default=False)
    
    def __str__(self):
        recipient = self.shared_with.username if self.shared_with else self.shared_with_email
        return f"Share link for {self.file.file_name} shared with {recipient}"
    
    def save(self, *args, **kwargs):
        # Set default expiration to 7 days from now if not provided
        if not self.expires_at and self.id is None:  # Only set on creation
            self.expires_at = datetime.now() + timedelta(days=7)
        
        # Set owner if not already set
        if not self.owner_id and self.file:
            self.owner = self.file.user
            
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if the link is still valid (active and not expired)"""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < datetime.now():
            return False
            
        return True

