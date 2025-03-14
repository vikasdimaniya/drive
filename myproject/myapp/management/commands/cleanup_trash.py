from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import FileMetadata
from django.conf import settings
import boto3

class Command(BaseCommand):
    help = 'Delete files that have been in trash for more than 30 days'

    def handle(self, *args, **options):
        # Initialize MinIO client
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        # Get files that have been in trash for more than 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        expired_files = FileMetadata.objects.filter(
            trashed=True,
            trash_date__lt=thirty_days_ago
        )
        
        count = 0
        for file in expired_files:
            try:
                # Delete the file from S3
                s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=file.file_path
                )
                
                # Delete the file metadata
                file.delete()
                count += 1
                
                self.stdout.write(f"Deleted: {file.file_name}")
            except Exception as e:
                self.stderr.write(f"Error deleting {file.file_name}: {str(e)}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} expired files from trash')) 