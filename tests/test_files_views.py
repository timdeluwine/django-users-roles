import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


@pytest.fixture(autouse=True)
def isolated_media_storage(settings, tmp_path):
    """Изолирует файловые операции тестов во временной папке."""
    test_media = tmp_path / "media_test"
    settings.MEDIA_ROOT = test_media
    settings.STORAGES["default"]["OPTIONS"]["location"] = test_media


@pytest.mark.django_db
def test_anonymous_user_redirected_to_login(client):
    response = client.get(reverse("file_manager"))
    assert response.status_code == 302
    assert "/login/" in response.url


@pytest.mark.django_db
def test_authenticated_user_access_file_manager(client, regular_user):
    client.force_login(regular_user)
    response = client.get(reverse("file_manager"))
    assert response.status_code == 200
    assert "Файловый менеджер" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_create_folder_and_navigation(client, regular_user):
    client.force_login(regular_user)

    resp = client.post(
        reverse("file_mkdir"),
        {"parent_path": "", "folder_name": "reports"},
        follow=True,
    )
    assert resp.status_code == 200
    assert "reports" in resp.content.decode("utf-8")

    sub_resp = client.get(reverse("file_manager"), {"path": "reports"})
    assert sub_resp.status_code == 200
    assert "Корень" in sub_resp.content.decode("utf-8")


@pytest.mark.django_db
def test_create_duplicate_folder_shows_error(client, regular_user):
    client.force_login(regular_user)
    client.post(reverse("file_mkdir"), {"parent_path": "", "folder_name": "archive"})
    resp = client.post(
        reverse("file_mkdir"),
        {"parent_path": "", "folder_name": "archive"},
        follow=True,
    )
    assert resp.status_code == 200
    assert "уже существует" in resp.content.decode("utf-8")


@pytest.mark.django_db
def test_upload_and_download_file(client, regular_user):
    client.force_login(regular_user)
    file_content = b"File download verification text"
    uploaded = SimpleUploadedFile("report.txt", file_content, content_type="text/plain")

    upload_resp = client.post(
        reverse("file_upload"),
        {"parent_path": "", "files": [uploaded]},
        follow=True,
    )
    assert upload_resp.status_code == 200
    assert "report.txt" in upload_resp.content.decode("utf-8")

    dl_resp = client.get(reverse("file_download"), {"path": "report.txt"})
    assert dl_resp.status_code == 200
    assert dl_resp.headers["Content-Disposition"].startswith("attachment;")
    assert b"".join(dl_resp.streaming_content) == file_content


@pytest.mark.django_db
def test_upload_empty_files_list(client, regular_user):
    client.force_login(regular_user)
    resp = client.post(
        reverse("file_upload"),
        {"parent_path": "", "files": []},
        follow=True,
    )
    assert resp.status_code == 200
    assert "Файлы для загрузки не выбраны" in resp.content.decode("utf-8")


@pytest.mark.django_db
def test_rename_item_view(client, regular_user):
    client.force_login(regular_user)
    client.post(reverse("file_mkdir"), {"parent_path": "", "folder_name": "old_name"})

    resp = client.post(
        reverse("file_rename"),
        {"item_path": "old_name", "new_name": "renamed_folder"},
        follow=True,
    )
    assert resp.status_code == 200
    assert "renamed_folder" in resp.content.decode("utf-8")


@pytest.mark.django_db
def test_delete_item_view(client, regular_user):
    client.force_login(regular_user)
    client.post(reverse("file_mkdir"), {"parent_path": "", "folder_name": "to_delete"})

    resp = client.post(
        reverse("file_delete"),
        {"item_path": "to_delete"},
        follow=True,
    )
    assert resp.status_code == 200
    assert "Элемент успешно удален" in resp.content.decode("utf-8")


@pytest.mark.django_db
def test_download_nonexistent_returns_404(client, regular_user):
    client.force_login(regular_user)
    resp = client.get(reverse("file_download"), {"path": "ghost.pdf"})
    assert resp.status_code == 404


@pytest.mark.django_db
def test_file_manager_path_traversal_returns_403(client, regular_user):
    client.force_login(regular_user)
    resp = client.get(reverse("file_manager"), {"path": "../../etc/passwd"})
    assert resp.status_code == 403
