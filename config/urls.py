from django.http import JsonResponse
from django.contrib import admin
from django.urls import include, path


def home(request):
    return JsonResponse(
        {
            "message": "Healthcare API is running",
            "endpoints": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/",
                "patients": "/api/patients/",
                "doctors": "/api/doctors/",
                "mappings": "/api/mappings/",
            },
        }
    )


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/doctors/", include("doctors.urls")),
    path("api/mappings/", include("mappings.urls")),
]