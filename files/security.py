import re
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import SuspiciousOperation


class StorageSecurityError(SuspiciousOperation):
    """Исключение при попытке Path Traversal или передаче опасных путей."""


class StorageValidationError(ValueError):
    """Ошибки пользовательской валидации (дубликат, лимит размера, пустое имя)."""


FORBIDDEN_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MAX_NAME_LENGTH = 255


def validate_item_name(name: str) -> str:
    """Проверяет и очищает имя одного файла или папки."""
    if not isinstance(name, str):
        raise StorageValidationError("Некорректный формат имени.")

    if "\x00" in name:
        raise StorageSecurityError("Обнаружен запрещенный null-байт в имени.")

    cleaned = name.strip()
    if not cleaned:
        raise StorageValidationError("Имя не может быть пустым.")

    if cleaned in (".", "..") or "/" in cleaned or "\\" in cleaned:
        raise StorageSecurityError("Недопустимое имя элемента (попытка обхода пути).")

    if len(cleaned) > MAX_NAME_LENGTH:
        raise StorageValidationError(
            f"Имя слишком длинное (максимум {MAX_NAME_LENGTH} символов)."
        )

    if FORBIDDEN_NAME_CHARS.search(cleaned):
        raise StorageValidationError("Имя содержит запрещенные спецсимволы.")

    return cleaned


def normalize_rel_path(rel_path: str | None) -> str:
    """Нормализует относительный путь и блокирует выход за пределы корня."""
    if not rel_path:
        return ""

    if "\x00" in rel_path:
        raise StorageSecurityError("Обнаружен null-байт в пути.")

    raw = rel_path.strip()
    if not raw or raw == ".":
        return ""

    if raw.startswith(("/", "\\")) or re.match(r"^[a-zA-Z]:", raw):
        raise StorageSecurityError("Абсолютные пути запрещены.")

    unified = raw.replace("\\", "/")
    parts = [part for part in unified.split("/") if part]

    validated_parts: list[str] = []
    for part in parts:
        if part in (".", ".."):
            raise StorageSecurityError("Обнаружена попытка Path Traversal (..).")
        validated_parts.append(validate_item_name(part))

    if not validated_parts:
        return ""

    return str(PurePosixPath(*validated_parts))


def resolve_safe_local_path(base_dir: Path, rel_path: str | None = "") -> Path:
    """Возвращает безопасный абсолютный путь внутри base_dir."""
    norm_rel = normalize_rel_path(rel_path)
    root = base_dir.resolve()
    target = (root / norm_rel).resolve() if norm_rel else root

    if not target.is_relative_to(root):
        raise StorageSecurityError("Выход за пределы корневой директории хранилища.")

    return target


def validate_file_size(file_size: int, current_total_size: int = 0) -> None:
    """Проверяет размер загружаемого файла и общую квоту хранилища."""
    max_file_bytes = getattr(settings, "MAX_FILE_SIZE_BYTES", 10 * 1024 * 1024)
    max_file_mb = getattr(settings, "MAX_FILE_SIZE_MB", 10)

    if file_size > max_file_bytes:
        raise StorageValidationError(
            f"Размер файла превышает допустимый лимит ({max_file_mb} МБ)."
        )

    max_total_bytes = getattr(settings, "MAX_TOTAL_STORAGE_BYTES", 100 * 1024 * 1024)
    max_total_mb = getattr(settings, "MAX_TOTAL_STORAGE_MB", 100)

    if current_total_size + file_size > max_total_bytes:
        raise StorageValidationError(
            f"Превышен общий лимит хранилища ({max_total_mb} МБ)."
        )
