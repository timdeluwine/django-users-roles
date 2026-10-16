# Users & Roles + File Manager (`django-users-roles`)

[![CI Pipeline](https://github.com/timdeluwine/django-users-roles/actions/workflows/ci.yml/badge.svg)](https://github.com/timdeluwine/django-users-roles/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Django](https://img.shields.io/badge/django-5.1+-green.svg)
![Playwright](https://img.shields.io/badge/playwright-e2e-orange.svg)
![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)

Веб-приложение на Django с ролевой моделью управления пользователями (`users`) и встроенным командным файловым менеджером (`files`) с поддержкой сменных хранилищ (**Local File System** и **Amazon S3**).

---

## 📋 Архитектура и функциональность

### 1. Пользователи и роли (`users`)
* **Авторизация:** вход и выход через стандартную систему аутентификации Django (`django.contrib.auth`).
* **Ролевая модель (RBAC):** роли `admin` и `user` на базе стандартных групп Django (создаются идемпотентной командой `python manage.py setup_roles`).
* **Управление пользователями (`/manage-users/`):** доступно только администраторам. Позволяет назначать и снимать роли с защитой от снятия прав администратора у самого себя. Ссылка в навигационном меню отображается только пользователям с ролью `admin`.

### 2. Файловый менеджер (`files`)
* **Обоснование схемы доступа:** Раздел файлового менеджера (`/files/`) открыт для всех авторизованных пользователей (`LoginRequiredMixin`), так как это общее рабочее пространство команды без многопользовательской изоляции, в то время как раздел управления ролями (`/manage-users/`) остаётся строго административным. Анонимные пользователи автоматически перенаправляются на страницу входа.
* **Возможности:**
  * Просмотр содержимого текущей директории (имя, тип, размер, дата изменения) и навигация по вложенным папкам через «хлебные крошки» (breadcrumbs).
  * Создание папок, переименование и рекурсивное удаление папок вместе с содержимым (с диалогом подтверждения в браузере).
  * Загрузка одного или нескольких файлов за раз, переименование, скачивание и удаление файлов с подтверждением.
* **Абстракция хранилища (`StorageBackend`):**
  * Вьюхи и шаблоны работают исключительно через единый контракт `StorageBackend` (`list_dir`, `make_dir`, `save_file`, `open_file`, `delete_file`, `delete_dir`, `rename`, `exists`) и не зависят от конкретной реализации.
  * `LocalStorage` — хранит файлы в локальной директории `MEDIA_ROOT`.
  * `S3Storage` — работает с объектным хранилищем Amazon S3 через `boto3` (эмулирует папки через префиксы `/` и рекурсивно оперирует ключами при переименовании и удалении).
* **Безопасность (`files/security.py`):**
  * **Path Traversal Protection:** строгая нормализация всех путей (`PurePosixPath` / `Path.resolve()`), блокирующая выход за пределы корня (`../`, `/etc/passwd`, абсолютные пути и символические ссылки) как для локального диска, так и для S3-ключей.
  * **Санитизация имён:** фильтрация null-байтов (`\x00`), управляющих символов, слешей в именах и проверка максимальной длины имени (до 255 символов).
  * **Контроль размера:** проверка лимита на один файл (`MAX_UPLOAD_SIZE`) и суммарный размер пакета загрузки (`MAX_TOTAL_UPLOAD_SIZE`) с выводом понятного сообщения об ошибке без падения сервера (500).
  * **Безопасная отдача файлов:** все скачиваемые файлы (включая потенциально исполняемые `.exe`, `.php`, `.sh`, `.html`) отдаются строго с заголовками `Content-Disposition: attachment` и `X-Content-Type-Options: nosniff`, исключая их исполнение браузером или сервером.

---

## ⚙️ Локальный запуск (пошаговая инструкция)

### 1. Клонирование репозитория и установка зависимостей
```bash
git clone [https://github.com/timdeluwine/django-users-roles.git](https://github.com/timdeluwine/django-users-roles.git)
cd django-users-roles
python -m venv venv
# Активация на Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Активация на Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt