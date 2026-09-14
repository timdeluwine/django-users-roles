from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


class AccessControlTests(TestCase):
    def setUp(self):
        # Подготовка данных перед каждым тестом
        self.admin_group = Group.objects.create(name="admin")
        self.user_group = Group.objects.create(name="user")

        self.regular_user = User.objects.create_user(
            username="regular", password="password123"
        )
        self.admin_user = User.objects.create_user(
            username="manager", password="password123"
        )
        self.admin_user.groups.add(self.admin_group)

    def test_anonymous_redirected_to_login(self):
        """Неавторизованного пользователя отправляет на логин"""
        response = self.client.get(reverse("manage_users"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_regular_user_gets_403_on_manage(self):
        """Обычный пользователь получает 403 Forbidden при попытке входа в /manage/"""
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("manage_users"))
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_manage(self):
        """Пользователь с ролью admin получает доступ 200 OK к /manage/"""
        self.client.login(username="manager", password="password123")
        response = self.client.get(reverse("manage_users"))
        self.assertEqual(response.status_code, 200)

    def test_assign_role_to_user(self):
        """Администратор может назначить роль пользователю через POST-запрос"""
        self.client.login(username="manager", password="password123")
        url = reverse("manage_user_role", args=[self.regular_user.id])
        response = self.client.post(url, {"role_name": "user", "action": "assign"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.regular_user.groups.filter(name="user").exists())
