from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import SharedLink
from django.db.models import Q

class Command(BaseCommand):
    help = 'Check shared links in the database and display their status'

    def handle(self, *args, **options):
        """
        This command checks all shared links in the database and displays their status.
        It's useful for debugging issues with shared files not appearing correctly.
        
        Usage: python manage.py check_shared_links
        """
        # Get all users
        users = User.objects.all()
        self.stdout.write(f"Total users: {users.count()}")
        
        for user in users:
            self.stdout.write(f"\nUser: {user.username}, Email: {user.email}")
            
            # Check shared links where this user is the recipient
            shared_with_user = SharedLink.objects.filter(
                Q(shared_with=user) | Q(shared_with_email=user.email),
                is_active=True
            )
            self.stdout.write(f"  Shared with {user.username}: {shared_with_user.count()} links")
            
            for link in shared_with_user:
                self.stdout.write(f"    - File: {link.file.file_name}, Shared by: {link.owner.username}, Valid: {link.is_valid}")
                self.stdout.write(f"      Token: {link.token}")
                self.stdout.write(f"      shared_with_user: {link.shared_with_id}, shared_with_email: {link.shared_with_email}")
            
            # Check shared links created by this user
            shared_by_user = SharedLink.objects.filter(owner=user)
            self.stdout.write(f"  Shared by {user.username}: {shared_by_user.count()} links")
            
            for link in shared_by_user:
                recipient = link.shared_with.username if link.shared_with else link.shared_with_email
                self.stdout.write(f"    - File: {link.file.file_name}, Shared with: {recipient}, Valid: {link.is_valid}")
                self.stdout.write(f"      Token: {link.token}")
                self.stdout.write(f"      shared_with_user: {link.shared_with_id}, shared_with_email: {link.shared_with_email}") 