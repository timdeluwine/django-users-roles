from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, TemplateView


# 1. Защитный миксин: пускает ТОЛЬКО суперпользователей или тех, кто в группе 'admin'
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="admin").exists()

    def handle_no_permission(self):
        # Если юзер залогинен, но он не админ — отдаем строгую 403 ошибку
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


# 2. Главная страница обычного пользователя
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"


# 3. Страница кастомной админки /manage/
class ManageUsersView(AdminRequiredMixin, ListView):
    model = User
    template_name = "manage_users.html"
    context_object_name = "users_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_roles"] = Group.objects.all()
        return context


# 4. Обработчик назначения и снятия роли
class ManageUserRoleView(AdminRequiredMixin, View):
    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        role_name = request.POST.get("role_name")
        action = request.POST.get("action")

        # ЗАЩИТА: Нельзя снять роль admin с самого себя
        if request.user == target_user and role_name == "admin" and action == "remove":
            messages.error(request, "Нельзя снять роль администратора с самого себя!")
            return redirect("manage_users")

        if role_name:
            role = get_object_or_404(Group, name=role_name)
            if action == "assign":
                target_user.groups.add(role)
                messages.success(request, f"Роль «{role_name}» назначена пользователю {target_user.username}.")
            elif action == "remove":
                target_user.groups.remove(role)
                messages.success(request, f"Роль «{role_name}» снята с пользователя {target_user.username}.")

        return redirect("manage_users")