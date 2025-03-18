from django.urls import path
from .views import upload_prescription

urlpatterns = [
    path("upload-prescription/", upload_prescription, name="upload_prescription"),
]