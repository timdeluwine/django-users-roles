from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse


class UsersAndRolesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_group = Group.objects.create(name="admin")
        self.user_group = Group.objects.create(name="user")

        self.admin_user = User.objects.create_user(
            username="admin_user",
            password="adminpassword123",
            first_name="Admin",
            last_name="System",
        )
        self.admin_user.groups.add(self.admin_group)

        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="userpassword123",
            first_name="Regular",
            last_name="Person",
        )
        self.regular_user.groups.add(self.user_group)

    def test_login_success(self):
        """Успешный вход перенаправляет в личный кабинет."""
        response = self.client.post(
            reverse("login"),
            {"username": "regular_user", "password": "userpassword123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_login_failure(self):
        """Неверный пароль возвращает форму с ошибкой без утечки данных."""
        response = self.client.post(
            reverse("login"),
            {"username": "regular_user", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверное имя пользователя или пароль")

    def test_logout(self):
        """Выход успешно завершает сессию и делает редирект."""
        self.client.login(username="regular_user", password="userpassword123")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        response_home = self.client.get(reverse("home"))
        self.assertEqual(response_home.status_code, 302)

    def test_admin_access_manage_view(self):
        """Администратор получает доступ (200) и видит имена и пользователей."""
        self.client.login(username="admin_user", password="adminpassword123")
        response = self.client.get(reverse("manage_users"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Панель управления")
        self.assertContains(response, "admin_user")
        self.assertContains(response, "Admin System")

    def test_regular_user_manage_view_forbidden(self):
        """Обычный пользователь получает 403 при попытке зайти в /manage/."""
        self.client.login(username="regular_user", password="userpassword123")
        response = self.client.get(reverse("manage_users"))
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_modify_roles_post(self):
        """Обычный пользователь не может менять роли через прямой POST-запрос, БД не меняется."""
        self.client.login(username="regular_user", password="userpassword123")
        url = reverse("manage_user_role", args=[self.regular_user.id])
        response = self.client.post(url, {"role_name": "admin", "action": "assign"})
        self.assertEqual(response.status_code, 403)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.groups.filter(name="admin").exists())

    def test_admin_assign_role(self):
        """Администратор успешно назначает роль, запись сохраняется в БД."""
        self.client.login(username="admin_user", password="adminpassword123")
        url = reverse("manage_user_role", args=[self.regular_user.id])
        response = self.client.post(url, {"role_name": "admin", "action": "assign"})
        self.assertEqual(response.status_code, 302)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.groups.filter(name="admin").exists())

    def test_admin_remove_role(self):
        """Администратор успешно снимает роль, изменения сохраняются в БД."""
        self.client.login(username="admin_user", password="adminpassword123")
        url = reverse("manage_user_role", args=[self.regular_user.id])
        response = self.client.post(url, {"role_name": "user", "action": "remove"})
        self.assertEqual(response.status_code, 302)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.groups.filter(name="user").exists())

    def test_admin_cannot_remove_own_admin_role(self):
        """Администратор не может снять роль admin с самого себя, роль в БД остается."""
        self.client.login(username="admin_user", password="adminpassword123")
        url = reverse("manage_user_role", args=[self.admin_user.id])
        response = self.client.post(url, {"role_name": "admin", "action": "remove"})
        self.assertEqual(response.status_code, 302)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.groups.filter(name="admin").exists())
