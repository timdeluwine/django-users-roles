from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from users.views import HomeView, ManageUserRoleView, ManageUsersView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", HomeView.as_view(), name="home"),
    path("manage/", ManageUsersView.as_view(), name="manage_users"),
    path(
        "manage/user/<int:user_id>/role/",
        ManageUserRoleView.as_view(),
        name="manage_user_role",
    ),
]
