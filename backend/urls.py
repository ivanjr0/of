from django.urls import path  # , include
from app.api import api

urlpatterns = [
    path("api/", api.urls),
    # path('django-rq/', include('django_rq.urls')),  # Temporarily disabled
]
