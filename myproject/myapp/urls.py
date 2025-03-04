from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dashboard, create_multipart_upload, get_part_presigned_url, complete_multipart_upload, list_user_files, get_presigned_url

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('dashboard/', dashboard, name='dashboard'),

    path("api/upload/multipart/start/", create_multipart_upload, name="start-multipart"),
    path("api/upload/multipart/part/", get_part_presigned_url, name="get-part-upload-url"),
    path("api/upload/multipart/complete/", complete_multipart_upload, name="complete-multipart"),
    
    path("api/user/files/", list_user_files, name="list-user-files"),
    path("api/user/file-url/", get_presigned_url, name="get-presigned-url"),
]

