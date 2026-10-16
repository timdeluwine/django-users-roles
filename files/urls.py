from django.urls import path

from files.views import (
    FileDownloadView,
    FileManagerView,
    FileUploadView,
    ItemDeleteView,
    ItemRenameView,
    MakeDirectoryView,
)

urlpatterns = [
    path("", FileManagerView.as_view(), name="file_manager"),
    path("mkdir/", MakeDirectoryView.as_view(), name="file_mkdir"),
    path("upload/", FileUploadView.as_view(), name="file_upload"),
    path("download/", FileDownloadView.as_view(), name="file_download"),
    path("rename/", ItemRenameView.as_view(), name="file_rename"),
    path("delete/", ItemDeleteView.as_view(), name="file_delete"),
]
