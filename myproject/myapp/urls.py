from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dashboard, create_multipart_upload, get_part_presigned_url, complete_multipart_upload, list_user_files, get_presigned_url, delete_user_file, search_user_files, signup

urlpatterns = [

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
]

