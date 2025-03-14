from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    dashboard, create_multipart_upload, get_part_presigned_url, complete_multipart_upload, 
    list_user_files, get_presigned_url, delete_user_file, search_user_files, signup, home, 
    create_shared_link, access_shared_file, list_shared_with_me, list_shared_by_me, revoke_access,
    refresh_shared_files, remove_shared_with_me
)

urlpatterns = [
    # Root URL
    path('', home, name='home'),

    # Authentication
    path('signup/', signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Upload files
    path("api/upload/multipart/start/", create_multipart_upload, name="start-multipart"),
    path("api/upload/multipart/part/", get_part_presigned_url, name="get-part-upload-url"),
    path("api/upload/multipart/complete/", complete_multipart_upload, name="complete-multipart"),
    
    # List user files
    path("api/user/files/", list_user_files, name="list-user-files"),
    path("api/user/file-url/", get_presigned_url, name="get-presigned-url"),

    # search user files
    path("api/user/search-files/", search_user_files, name="search-user-files"),

    # Delete user file
    path("api/user/delete-file/", delete_user_file, name="delete-user-file"),
    
    # Shared links
    path("api/user/create-shared-link/", create_shared_link, name="create-shared-link"),
    path("shared/<uuid:token>/", access_shared_file, name="access-shared-file"),
    path("api/user/shared-with-me/", list_shared_with_me, name="shared-with-me"),
    path("api/user/shared-by-me/", list_shared_by_me, name="shared-by-me"),
    path("api/user/revoke-access/", revoke_access, name="revoke-access"),
    path("api/user/remove-shared-with-me/", remove_shared_with_me, name="remove-shared-with-me"),
    path("api/user/refresh-shared-files/", refresh_shared_files, name="refresh-shared-files"),
]

