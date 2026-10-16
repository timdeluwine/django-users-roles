import tempfile
from pathlib import Path

import boto3
import pytest
from django.contrib.auth.models import Group, User
from moto import mock_aws

from files.storage import LocalStorage, S3Storage


@pytest.fixture
def regular_user(db):
    user = User.objects.create_user(
        username="user1", password="password123", email="user1@example.com"
    )
    user_group, _ = Group.objects.get_or_create(name="user")
    user.groups.add(user_group)
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username="admin1", password="password123", email="admin1@example.com"
    )
    admin_group, _ = Group.objects.get_or_create(name="admin")
    user.groups.add(admin_group)
    return user


@pytest.fixture
def local_storage():
    """Изолированное временное локальное хранилище."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorage(base_dir=Path(temp_dir))
        yield storage


@pytest.fixture
def s3_storage():
    """Изолированное хранилище S3 на базе эмулятора moto."""
    with mock_aws():
        bucket_name = "test-e2e-bucket"
        s3_client = boto3.client("s3", region_name="eu-central-1")
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
        )
        storage = S3Storage(
            bucket_name=bucket_name,
            region_name="eu-central-1",
            access_key="mock_key",
            secret_key="mock_secret",
        )
        yield storage
