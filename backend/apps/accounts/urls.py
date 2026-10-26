"""URL routing for Authentication, Identity, and Role Administration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.accounts.views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RoleListView,
    TokenRefreshView,
    UserAdminViewSet,
)

router = DefaultRouter()
router.register(r"users", UserAdminViewSet, basename="admin-user")

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", CurrentUserView.as_view(), name="auth-me"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
    path("password/reset/request/", PasswordResetRequestView.as_view(), name="auth-password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("roles/", RoleListView.as_view(), name="auth-roles"),
    path("", include(router.urls)),
]
