import io
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from files.security import (
    StorageValidationError,
    normalize_rel_path,
    resolve_safe_local_path,
    validate_file_size,
    validate_item_name,
)


@dataclass
class StorageItem:
    name: str
    path: str
    is_dir: bool
    size: int = 0
    modified_at: datetime | None = None


class StorageBackend(ABC):
    """Единый интерфейс хранилища файлов и папок."""

    @abstractmethod
    def list_dir(self, rel_path: str = "") -> list[StorageItem]:
        """Возвращает содержимое папки (сначала папки, затем файлы)."""

    @abstractmethod
    def make_dir(self, parent_path: str, folder_name: str) -> str:
        """Создает новую папку внутри parent_path."""

    @abstractmethod
    def save(self, parent_path: str, filename: str, file_obj: BinaryIO) -> str:
        """Сохраняет файл в указанную папку."""

    @abstractmethod
    def open(self, rel_path: str) -> BinaryIO:
        """Открывает файл для чтения (скачивания)."""

    @abstractmethod
    def delete(self, rel_path: str) -> None:
        """Удаляет файл или рекурсивно удаляет папку со всем содержимым."""

    @abstractmethod
    def rename(self, rel_path: str, new_name: str) -> str:
        """Переименовывает файл или папку."""

    @abstractmethod
    def exists(self, rel_path: str) -> bool:
        """Проверяет существование файла или папки."""

    @abstractmethod
    def is_dir(self, rel_path: str) -> bool:
        """Проверяет, является ли путь папкой."""

    @abstractmethod
    def get_total_size(self) -> int:
        """Возвращает суммарный размер всех файлов в хранилище (в байтах)."""


class LocalStorage(StorageBackend):
    """Реализация хранилища на локальной файловой системе."""

    def __init__(self, base_dir: Path | str | None = None):
        if base_dir is None:
            default_opts = settings.STORAGES.get("default", {}).get("OPTIONS", {})
            base_dir = default_opts.get("location") or settings.MEDIA_ROOT
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, rel_path: str = "") -> Path:
        return resolve_safe_local_path(self.base_dir, rel_path)

    def exists(self, rel_path: str) -> bool:
        target = self._resolve(rel_path)
        return target.exists()

    def is_dir(self, rel_path: str) -> bool:
        target = self._resolve(rel_path)
        return target.is_dir()

    def get_total_size(self) -> int:
        total = 0
        for item in self.base_dir.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return total

    def list_dir(self, rel_path: str = "") -> list[StorageItem]:
        norm_parent = normalize_rel_path(rel_path)
        target_dir = self._resolve(norm_parent)

        if not target_dir.exists() or not target_dir.is_dir():
            raise FileNotFoundError("Папка не найдена.")

        items: list[StorageItem] = []
        for entry in target_dir.iterdir():
            stat = entry.stat()
            item_rel = f"{norm_parent}/{entry.name}" if norm_parent else entry.name
            is_directory = entry.is_dir()
            items.append(
                StorageItem(
                    name=entry.name,
                    path=item_rel,
                    is_dir=is_directory,
                    size=0 if is_directory else stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                )
            )

        items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        return items

    def make_dir(self, parent_path: str, folder_name: str) -> str:
        norm_parent = normalize_rel_path(parent_path)
        clean_name = validate_item_name(folder_name)
        parent_dir = self._resolve(norm_parent)

        if not parent_dir.exists() or not parent_dir.is_dir():
            raise FileNotFoundError("Родительская папка не существует.")

        new_rel = f"{norm_parent}/{clean_name}" if norm_parent else clean_name
        target_dir = self._resolve(new_rel)

        if target_dir.exists():
            raise StorageValidationError(
                f'Папка или файл с именем "{clean_name}" уже существует.'
            )

        target_dir.mkdir(parents=False, exist_ok=False)
        return new_rel

    def save(self, parent_path: str, filename: str, file_obj: BinaryIO) -> str:
        norm_parent = normalize_rel_path(parent_path)
        clean_name = validate_item_name(filename)
        parent_dir = self._resolve(norm_parent)

        if not parent_dir.exists() or not parent_dir.is_dir():
            raise FileNotFoundError("Целевая папка не найдена.")

        file_obj.seek(0, io.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)

        validate_file_size(file_size, self.get_total_size())

        new_rel = f"{norm_parent}/{clean_name}" if norm_parent else clean_name
        target_file = self._resolve(new_rel)

        if target_file.exists():
            raise StorageValidationError(f'Элемент "{clean_name}" уже существует.')

        with open(target_file, "wb") as dest:
            shutil.copyfileobj(file_obj, dest)

        return new_rel

    def open(self, rel_path: str) -> BinaryIO:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel:
            raise FileNotFoundError("Не указан путь к файлу.")

        target_file = self._resolve(norm_rel)
        if not target_file.exists() or not target_file.is_file():
            raise FileNotFoundError("Файл не найден.")

        return open(target_file, "rb")

    def delete(self, rel_path: str) -> None:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel:
            raise StorageValidationError("Нельзя удалить корневую директорию.")

        target = self._resolve(norm_rel)
        if not target.exists():
            raise FileNotFoundError("Элемент не найден.")

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    def rename(self, rel_path: str, new_name: str) -> str:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel:
            raise StorageValidationError("Нельзя переименовать корневую директорию.")

        clean_new_name = validate_item_name(new_name)
        source = self._resolve(norm_rel)
        if not source.exists():
            raise FileNotFoundError("Исходный элемент не найден.")

        parent_rel = "/".join(norm_rel.split("/")[:-1]) if "/" in norm_rel else ""
        new_rel = f"{parent_rel}/{clean_new_name}" if parent_rel else clean_new_name
        target = self._resolve(new_rel)

        if target.exists():
            raise StorageValidationError(
                f'Элемент с именем "{clean_new_name}" уже существует.'
            )

        source.rename(target)
        return new_rel


class S3Storage(StorageBackend):
    """Реализация хранилища в Amazon S3."""

    def __init__(
        self,
        bucket_name: str | None = None,
        region_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
    ):
        opts = settings.STORAGES.get("default", {}).get("OPTIONS", {})
        self.bucket_name = (
            bucket_name
            or opts.get("bucket_name")
            or getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        )
        if not self.bucket_name:
            raise StorageValidationError(
                "Не задано имя S3-бакета (AWS_STORAGE_BUCKET_NAME)."
            )

        region = (
            region_name
            or opts.get("region_name")
            or getattr(settings, "AWS_S3_REGION_NAME", "eu-central-1")
        )
        ak = (
            access_key
            or opts.get("access_key")
            or getattr(settings, "AWS_ACCESS_KEY_ID", None)
        )
        sk = (
            secret_key
            or opts.get("secret_key")
            or getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        )
        endpoint = (
            endpoint_url
            or opts.get("endpoint_url")
            or getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        )

        client_kwargs: dict = {"region_name": region}
        if ak and sk:
            client_kwargs["aws_access_key_id"] = ak
            client_kwargs["aws_secret_access_key"] = sk
        if endpoint:
            client_kwargs["endpoint_url"] = endpoint

        self.client = boto3.client("s3", **client_kwargs)

    def _file_exists(self, norm_rel: str) -> bool:
        if not norm_rel:
            return False
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=norm_rel)
            return True
        except ClientError:
            return False

    def _dir_exists(self, norm_rel: str) -> bool:
        if not norm_rel:
            return True
        prefix = f"{norm_rel}/"
        resp = self.client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=prefix, MaxKeys=1
        )
        return resp.get("KeyCount", 0) > 0

    def exists(self, rel_path: str) -> bool:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel:
            return True
        return self._file_exists(norm_rel) or self._dir_exists(norm_rel)

    def is_dir(self, rel_path: str) -> bool:
        norm_rel = normalize_rel_path(rel_path)
        return self._dir_exists(norm_rel)

    def get_total_size(self) -> int:
        total = 0
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name):
            for obj in page.get("Contents", []):
                if not obj["Key"].endswith("/"):
                    total += obj.get("Size", 0)
        return total

    def list_dir(self, rel_path: str = "") -> list[StorageItem]:
        norm_parent = normalize_rel_path(rel_path)
        if norm_parent and not self._dir_exists(norm_parent):
            raise FileNotFoundError("Папка не найдена.")

        prefix = f"{norm_parent}/" if norm_parent else ""
        paginator = self.client.get_paginator("list_objects_v2")
        items: list[StorageItem] = []
        seen_dirs: set[str] = set()

        for page in paginator.paginate(
            Bucket=self.bucket_name, Prefix=prefix, Delimiter="/"
        ):
            for common_prefix in page.get("CommonPrefixes", []):
                dir_key = common_prefix["Prefix"].rstrip("/")
                dir_name = dir_key.split("/")[-1]
                if dir_name and dir_name not in seen_dirs:
                    seen_dirs.add(dir_name)
                    items.append(
                        StorageItem(
                            name=dir_name,
                            path=dir_key,
                            is_dir=True,
                            size=0,
                            modified_at=None,
                        )
                    )

            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key == prefix or key.endswith("/"):
                    continue
                file_name = key[len(prefix) :]
                if "/" in file_name:
                    continue
                items.append(
                    StorageItem(
                        name=file_name,
                        path=key,
                        is_dir=False,
                        size=obj.get("Size", 0),
                        modified_at=obj.get("LastModified"),
                    )
                )

        items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        return items

    def make_dir(self, parent_path: str, folder_name: str) -> str:
        norm_parent = normalize_rel_path(parent_path)
        clean_name = validate_item_name(folder_name)

        if norm_parent and not self._dir_exists(norm_parent):
            raise FileNotFoundError("Родительская папка не существует.")

        new_rel = f"{norm_parent}/{clean_name}" if norm_parent else clean_name
        if self.exists(new_rel):
            raise StorageValidationError(
                f'Папка или файл с именем "{clean_name}" уже существует.'
            )

        self.client.put_object(Bucket=self.bucket_name, Key=f"{new_rel}/", Body=b"")
        return new_rel

    def save(self, parent_path: str, filename: str, file_obj: BinaryIO) -> str:
        norm_parent = normalize_rel_path(parent_path)
        clean_name = validate_item_name(filename)

        if norm_parent and not self._dir_exists(norm_parent):
            raise FileNotFoundError("Целевая папка не найдена.")

        file_obj.seek(0, io.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)

        validate_file_size(file_size, self.get_total_size())

        new_rel = f"{norm_parent}/{clean_name}" if norm_parent else clean_name
        if self.exists(new_rel):
            raise StorageValidationError(f'Элемент "{clean_name}" уже существует.')

        data = file_obj.read()
        self.client.put_object(Bucket=self.bucket_name, Key=new_rel, Body=data)
        return new_rel

    def open(self, rel_path: str) -> BinaryIO:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel or not self._file_exists(norm_rel):
            raise FileNotFoundError("Файл не найден.")

        resp = self.client.get_object(Bucket=self.bucket_name, Key=norm_rel)
        return io.BytesIO(resp["Body"].read())

    def delete(self, rel_path: str) -> None:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel:
            raise StorageValidationError("Нельзя удалить корневую директорию.")

        if self._file_exists(norm_rel):
            self.client.delete_object(Bucket=self.bucket_name, Key=norm_rel)
            return

        if self._dir_exists(norm_rel):
            prefix = f"{norm_rel}/"
            paginator = self.client.get_paginator("list_objects_v2")
            keys_to_delete = []
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys_to_delete.append({"Key": obj["Key"]})

            for i in range(0, len(keys_to_delete), 1000):
                batch = keys_to_delete[i : i + 1000]
                self.client.delete_objects(
                    Bucket=self.bucket_name, Delete={"Objects": batch}
                )
            return

        raise FileNotFoundError("Элемент не найден.")

    def rename(self, rel_path: str, new_name: str) -> str:
        norm_rel = normalize_rel_path(rel_path)
        if not norm_rel:
            raise StorageValidationError("Нельзя переименовать корневую директорию.")

        clean_new_name = validate_item_name(new_name)
        parent_rel = "/".join(norm_rel.split("/")[:-1]) if "/" in norm_rel else ""
        new_rel = f"{parent_rel}/{clean_new_name}" if parent_rel else clean_new_name

        if self.exists(new_rel):
            raise StorageValidationError(
                f'Элемент с именем "{clean_new_name}" уже существует.'
            )

        if self._file_exists(norm_rel):
            self.client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": norm_rel},
                Key=new_rel,
            )
            self.client.delete_object(Bucket=self.bucket_name, Key=norm_rel)
            return new_rel

        if self._dir_exists(norm_rel):
            old_prefix = f"{norm_rel}/"
            new_prefix = f"{new_rel}/"
            paginator = self.client.get_paginator("list_objects_v2")
            old_keys: list[str] = []

            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=old_prefix):
                for obj in page.get("Contents", []):
                    old_keys.append(obj["Key"])

            for old_key in old_keys:
                suffix = old_key[len(old_prefix) :]
                target_key = f"{new_prefix}{suffix}"
                self.client.copy_object(
                    Bucket=self.bucket_name,
                    CopySource={"Bucket": self.bucket_name, "Key": old_key},
                    Key=target_key,
                )

            for i in range(0, len(old_keys), 1000):
                batch = [{"Key": k} for k in old_keys[i : i + 1000]]
                self.client.delete_objects(
                    Bucket=self.bucket_name, Delete={"Objects": batch}
                )
            return new_rel

        raise FileNotFoundError("Исходный элемент не найден.")


def get_storage_backend() -> StorageBackend:
    """Фабрика, возвращающая активный StorageBackend на основе настроек Django."""
    backend_path = settings.STORAGES.get("default", {}).get("BACKEND", "")
    storage_mode = getattr(settings, "STORAGE_BACKEND", "local").lower()

    if storage_mode == "s3" or "s3boto3" in backend_path.lower():
        return S3Storage()
    return LocalStorage()
