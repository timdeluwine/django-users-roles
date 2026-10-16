import mimetypes
from urllib.parse import quote, urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from files.security import (
    StorageSecurityError,
    StorageValidationError,
    normalize_rel_path,
)
from files.storage import get_storage_backend


def build_breadcrumbs(current_path: str) -> list[dict[str, str]]:
    """Формирует список хлебных крошек для навигации."""
    breadcrumbs = [{"name": "Корень", "path": ""}]
    if not current_path:
        return breadcrumbs

    accumulated: list[str] = []
    for part in current_path.split("/"):
        if part:
            accumulated.append(part)
            breadcrumbs.append({"name": part, "path": "/".join(accumulated)})
    return breadcrumbs


class FileManagerView(LoginRequiredMixin, View):
    """Главная страница файлового менеджера: просмотр папки и хлебные крошки."""

    template_name = "files/manager.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        storage = get_storage_backend()
        raw_path = request.GET.get("path", "")

        try:
            current_path = normalize_rel_path(raw_path)
            items = storage.list_dir(current_path)
        except (StorageSecurityError, SuspiciousOperation):
            raise PermissionDenied("Недопустимый путь.")
        except FileNotFoundError:
            raise Http404("Папка не найдена.")

        context = {
            "current_path": current_path,
            "breadcrumbs": build_breadcrumbs(current_path),
            "items": items,
        }
        return render(request, self.template_name, context)


class MakeDirectoryView(LoginRequiredMixin, View):
    """Создание новой папки внутри текущей директории."""

    def post(self, request: HttpRequest) -> HttpResponse:
        storage = get_storage_backend()
        parent_path = request.POST.get("parent_path", "")
        folder_name = request.POST.get("folder_name", "")

        try:
            storage.make_dir(parent_path, folder_name)
            messages.success(request, f'Папка "{folder_name}" успешно создана.')
        except (StorageSecurityError, SuspiciousOperation):
            raise PermissionDenied("Попытка недопустимой операции с путем.")
        except (StorageValidationError, FileNotFoundError) as err:
            messages.error(request, str(err))

        norm_parent = normalize_rel_path(parent_path)
        url = reverse("file_manager")
        if norm_parent:
            url += f"?{urlencode({'path': norm_parent})}"
        return redirect(url)


class FileUploadView(LoginRequiredMixin, View):
    """Загрузка одного или нескольких файлов в текущую папку."""

    def post(self, request: HttpRequest) -> HttpResponse:
        storage = get_storage_backend()
        parent_path = request.POST.get("parent_path", "")
        files = request.FILES.getlist("files")

        if not files:
            messages.error(request, "Файлы для загрузки не выбраны.")
            norm_parent = normalize_rel_path(parent_path)
            url = reverse("file_manager")
            if norm_parent:
                url += f"?{urlencode({'path': norm_parent})}"
            return redirect(url)

        uploaded_count = 0
        for uploaded_file in files:
            try:
                storage.save(parent_path, uploaded_file.name, uploaded_file)
                uploaded_count += 1
            except (StorageSecurityError, SuspiciousOperation):
                raise PermissionDenied("Попытка загрузки по недопустимому пути.")
            except StorageValidationError as err:
                messages.error(
                    request, f'Ошибка при загрузке "{uploaded_file.name}": {err}'
                )

        if uploaded_count > 0:
            messages.success(request, f"Успешно загружено файлов: {uploaded_count}.")

        norm_parent = normalize_rel_path(parent_path)
        url = reverse("file_manager")
        if norm_parent:
            url += f"?{urlencode({'path': norm_parent})}"
        return redirect(url)


class FileDownloadView(LoginRequiredMixin, View):
    """Безопасное скачивание файла (Content-Disposition: attachment)."""

    def get(self, request: HttpRequest) -> HttpResponse:
        storage = get_storage_backend()
        file_path = request.GET.get("path", "")

        try:
            norm_path = normalize_rel_path(file_path)
            if not norm_path or storage.is_dir(norm_path):
                raise Http404("Файл не найден.")

            file_stream = storage.open(norm_path)
            file_name = norm_path.split("/")[-1]
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = "application/octet-stream"

            response = FileResponse(
                file_stream, content_type=content_type, as_attachment=True
            )
            # Защита от выполнения в браузере и поддержка unicode-имен
            encoded_name = quote(file_name)
            response["Content-Disposition"] = (
                f"attachment; filename=\"{encoded_name}\"; filename*=UTF-8''{encoded_name}"
            )
            return response
        except (StorageSecurityError, SuspiciousOperation):
            raise PermissionDenied("Недопустимый путь к файлу.")
        except FileNotFoundError:
            raise Http404("Файл не найден.")


class ItemRenameView(LoginRequiredMixin, View):
    """Переименование файла или папки."""

    def post(self, request: HttpRequest) -> HttpResponse:
        storage = get_storage_backend()
        item_path = request.POST.get("item_path", "")
        new_name = request.POST.get("new_name", "")

        try:
            storage.rename(item_path, new_name)
            messages.success(request, f'Элемент успешно переименован в "{new_name}".')
        except (StorageSecurityError, SuspiciousOperation):
            raise PermissionDenied("Недопустимая операция переименования.")
        except (StorageValidationError, FileNotFoundError) as err:
            messages.error(request, str(err))

        parent_path = "/".join(item_path.split("/")[:-1]) if "/" in item_path else ""
        url = reverse("file_manager")
        if parent_path:
            url += f"?{urlencode({'path': parent_path})}"
        return redirect(url)


class ItemDeleteView(LoginRequiredMixin, View):
    """Удаление файла или рекурсивное удаление папки."""

    def post(self, request: HttpRequest) -> HttpResponse:
        storage = get_storage_backend()
        item_path = request.POST.get("item_path", "")

        try:
            storage.delete(item_path)
            messages.success(request, "Элемент успешно удален.")
        except (StorageSecurityError, SuspiciousOperation):
            raise PermissionDenied("Недопустимый путь для удаления.")
        except (StorageValidationError, FileNotFoundError) as err:
            messages.error(request, str(err))

        parent_path = "/".join(item_path.split("/")[:-1]) if "/" in item_path else ""
        url = reverse("file_manager")
        if parent_path:
            url += f"?{urlencode({'path': parent_path})}"
        return redirect(url)
