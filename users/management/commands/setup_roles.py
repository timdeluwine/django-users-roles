from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Создает базовые роли (группы) admin и user'

    def handle(self, *args, **options):
        roles = ['admin', 'user']
        for role_name in roles:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Роль "{role_name}" успешно создана.'))
            else:
                self.stdout.write(self.style.WARNING(f'Роль "{role_name}" уже существует.'))