from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import SharedLink
from django.db.models import Q

class Command(BaseCommand):
    help = 'Fix shared links by associating them with the correct users'

    def handle(self, *args, **options):
        """
        This command finds shared links that are not properly associated with user accounts
        and fixes them by setting the shared_with field to the correct user.
        
        It's useful for fixing issues where shared files don't appear in the "Shared with me" section.
        
        Usage: python manage.py fix_shared_links
        """
        # Get all users
        users = User.objects.all()
        self.stdout.write(f"Total users: {users.count()}")
        
        total_fixed = 0
        
        for user in users:
            self.stdout.write(f"\nProcessing user: {user.username}, Email: {user.email}")
            
            # Find shared links that match the user's email OR username but aren't associated with the user
            query = Q()
            if user.email:
                query |= Q(shared_with_email=user.email)
            
            # Also try with username as email (for users without explicit email set)
            query |= Q(shared_with_email=user.username)
            
            shared_links = SharedLink.objects.filter(
                query,
                shared_with__isnull=True,
                is_active=True
            )
            
            count = shared_links.count()
            self.stdout.write(f"  Found {count} unassociated shared links for user {user.username}")
            
            # Associate each link with the user
            for link in shared_links:
                link.shared_with = user
                link.save()
                self.stdout.write(f"    - Associated shared file '{link.file.file_name}' with user {user.username}")
                total_fixed += 1
        
        self.stdout.write(f"\nTotal fixed links: {total_fixed}") 