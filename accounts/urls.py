from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    # Extra: exchange a refresh token for a new access token.
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
