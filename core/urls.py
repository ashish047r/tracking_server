from django.urls import path
from .views import get_suffix, get_batch_suffix

urlpatterns = [
    path("script/suffix/", get_suffix),
    path("script/batch_suffix/", get_batch_suffix),
]
