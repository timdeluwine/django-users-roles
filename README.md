# Users & Roles (Кастомная админка + аутентификация на Django)

Веб-приложение для управления учетными записями и распределения системных ролей через кастомную панель управления.

## Стек технологий
* Python 3.12
* Django 5.x
* База данных: SQLite
* Frontend: Django Templates (Server-Side Rendering)
* Линтинг и форматирование: Black, Ruff

---

## Архитектура: Что взято из Django vs Что написано самостоятельно

### Взято из Django (из коробки):
* Встроенная подсистема аутентификации и сессий (`django.contrib.auth`).
* Стандартная модель пользователя (`django.contrib.auth.models.User`).
* Хеширование паролей (алгоритм PBKDF2/SHA256, открытый текст в БД исключен).
* Роли на базе встроенной модели групп (`django.contrib.auth.models.Group`).
* Защита от CSRF-атак на формах (`{% csrf_token %}`).
* Классы представлений `LoginView`, `LogoutView`, `ListView`, `TemplateView`, `View`.

### Написано самостоятельно:
* `AdminRequiredMixin` — базовый миксин (`LoginRequiredMixin` + `UserPassesTestMixin`), блокирующий доступ к админке для обычных пользователей со статусом 403 Forbidden.
* `users.context_processors.admin_access` — контекстный процессор для единообразного отображения административного меню по тем же правилам, что и на сервере.
* Кастомная панель управления `/manage/` (`ManageUsersView`) со списком пользователей (включая `get_full_name`), ролей и статуса активности.
* Обработчик назначения и снятия ролей (`ManageUserRoleView`).
* Механизм защиты от случайного снятия роли `admin` с текущего пользователя с выводом уведомления через `messages`.
* Кастомная management-команда `setup_roles` для инициализации базовых групп `admin` и `user`.
* Комплекс автотестов (`users/tests.py`), проверяющий права доступа, статус-коды и реальные изменения в БД.

---

## Быстрый старт и запуск проекта с нуля

### 1. Клонирование и настройка виртуального окружения

    git clone https://github.com/timdeluwine/django-users-roles.git
    cd django-users-roles
    python -m venv venv

    # Активация в Windows (PowerShell):
    .\venv\Scripts\activate

    # Активация в Linux / macOS:
    source venv/bin/activate

    pip install -r requirements.txt

### 2. Настройка переменных окружения (.env)
Скопируйте шаблон `.env.example` в рабочий файл `.env`:

    # Windows (PowerShell):
    Copy-Item .env.example .env

    # Linux / macOS:
    cp .env.example .env

При необходимости отредактируйте значения `SECRET_KEY` и `DEBUG` в файле `.env` (без `SECRET_KEY` приложение не запустится).

### 3. Применение миграций, создание ролей и суперпользователя

    python manage.py migrate
    python manage.py setup_roles
    python manage.py createsuperuser

### 4. Запуск сервера разработки

    python manage.py runserver

После запуска приложение доступно по адресу: http://127.0.0.1:8000/
Панель управления доступна администраторам по адресу: http://127.0.0.1:8000/manage/

### 5. Запуск автоматических тестов

    python manage.py test

### 6. Проверка форматирования и линтера

    black --check .
    ruff check .