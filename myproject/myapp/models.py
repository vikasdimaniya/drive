from django.db import models
from django.contrib.auth.models import User

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

