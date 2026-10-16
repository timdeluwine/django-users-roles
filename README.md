# Django File Management System with RBAC

[![CI Pipeline](https://github.com/timdeluwine/django-users-roles/actions/workflows/ci.yml/badge.svg)](https://github.com/timdeluwine/django-users-roles/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Django](https://img.shields.io/badge/django-5.1-green.svg)
![Playwright](https://img.shields.io/badge/playwright-e2e-orange.svg)
![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)

Полнофункциональная система управления файлами и каталогами на базе Django с ролевой моделью доступа (RBAC), поддержкой сменных бэкендов хранилища (локальная файловая система / AWS S3) и автоматизированным CI/CD пайплайном.

---

## 🛠 Технологический стек

* **Бэкенд:** Python 3.12, Django 5.1
* **Хранилище:** Local File Storage / AWS S3 (`boto3`, `django-storages`)
* **Тестирование бэкенда:** Pytest, Pytest-Django, Pytest-Cov (покрытие 87%), Moto (S3-мок)
* **E2E-тестирование:** Playwright (TypeScript, Page Object Model)
* **Линтеры и форматирование:** Ruff, Black
* **CI/CD:** GitHub Actions

---

## 🚀 Архитектурные особенности

1. **Ролевая модель доступа (RBAC):**
   * Разграничение ролей `admin` (полный доступ к файлам и управлению ролями) и `user` (работа в изолированной директории).
   * Автоматическая инициализация через менеджмент-команду `python manage.py setup_roles`.

2. **Абстракция хранилища (Storage Engine):**
   * Единый контракт `StorageBackend` для `LocalStorage` и `S3Storage`.
   * Защита от атак выхода за пределы корневого каталога (Path Traversal Protection).
   * Потоковая загрузка, скачивание, создание вложенных директорий и рекурсивное удаление.

3. **Комплексное тестирование:**
   * **31 Unit/Contract тест:** валидация поведения хранилищ и представлений в памяти с эмуляцией AWS S3 через `moto`.
   * **7 E2E Playwright тестов:** браузерная проверка авторизации, работы с папками и манипуляций с файлами.

---

## ⚙️ Локальный запуск

### 1. Клонирование и виртуальное окружение
```bash
git clone [https://github.com/timdeluwine/django-users-roles.git](https://github.com/timdeluwine/django-users-roles.git)
cd django-users-roles
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt