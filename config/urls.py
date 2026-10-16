from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from users.views import HomeView, ManageUserRoleView, ManageUsersView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", HomeView.as_view(), name="home"),
    path("manage/", ManageUsersView.as_view(), name="manage_users"),
    path(
        "manage/role/<int:user_id>/",
        ManageUserRoleView.as_view(),
        name="manage_user_role",
    ),
    path("files/", include("files.urls")),
]
