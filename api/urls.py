from django.urls import path

from api.v1.views.uploader import FileUploadView

urlpatterns = [
    # Define your URL patterns here
    path('upload-file/', FileUploadView.as_view(), name='upload-file'),
]
