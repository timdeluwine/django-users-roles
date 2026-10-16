import io

import pytest

from files.security import StorageSecurityError, StorageValidationError


@pytest.mark.parametrize("storage_fixture", ["local_storage", "s3_storage"])
def test_storage_create_folder_and_list(request, storage_fixture):
    storage = request.getfixturevalue(storage_fixture)

    items = storage.list_dir("")
    assert len(items) == 0

    storage.make_dir("", "documents")
    items = storage.list_dir("")
    assert len(items) == 1
    assert items[0].name == "documents"
    assert items[0].is_dir is True

    storage.make_dir("documents", "archive")
    sub_items = storage.list_dir("documents")
    assert len(sub_items) == 1
    assert sub_items[0].name == "archive"
    assert sub_items[0].is_dir is True


@pytest.mark.parametrize("storage_fixture", ["local_storage", "s3_storage"])
def test_storage_duplicate_folder_error(request, storage_fixture):
    storage = request.getfixturevalue(storage_fixture)
    storage.make_dir("", "finance")

    with pytest.raises(StorageValidationError, match="уже существует"):
        storage.make_dir("", "finance")


@pytest.mark.parametrize("storage_fixture", ["local_storage", "s3_storage"])
def test_storage_save_open_and_delete_file(request, storage_fixture):
    storage = request.getfixturevalue(storage_fixture)
    content = b"Contract test payload"

    saved_path = storage.save("", "sample.txt", io.BytesIO(content))
    assert saved_path == "sample.txt"
    assert storage.exists("sample.txt") is True
    assert storage.is_dir("sample.txt") is False

    with storage.open("sample.txt") as stream:
        assert stream.read() == content

    storage.delete("sample.txt")
    assert storage.exists("sample.txt") is False


@pytest.mark.parametrize("storage_fixture", ["local_storage", "s3_storage"])
def test_storage_recursive_delete_folder(request, storage_fixture):
    storage = request.getfixturevalue(storage_fixture)
    storage.make_dir("", "projects")
    storage.make_dir("projects", "v1")
    storage.save("projects/v1", "code.py", io.BytesIO(b"print('hello')"))

    assert storage.exists("projects/v1/code.py") is True
    storage.delete("projects")
    assert storage.exists("projects") is False
    assert storage.exists("projects/v1/code.py") is False


@pytest.mark.parametrize("storage_fixture", ["local_storage", "s3_storage"])
def test_storage_rename_file_and_folder(request, storage_fixture):
    storage = request.getfixturevalue(storage_fixture)
    storage.make_dir("", "old_dir")
    storage.save("old_dir", "notes.txt", io.BytesIO(b"memo"))

    storage.rename("old_dir/notes.txt", "notes_v2.txt")
    assert storage.exists("old_dir/notes_v2.txt") is True
    assert storage.exists("old_dir/notes.txt") is False

    storage.rename("old_dir", "new_dir")
    assert storage.exists("new_dir") is True
    assert storage.exists("old_dir") is False
    assert storage.exists("new_dir/notes_v2.txt") is True


@pytest.mark.parametrize("storage_fixture", ["local_storage", "s3_storage"])
def test_storage_path_traversal_blocked(request, storage_fixture):
    storage = request.getfixturevalue(storage_fixture)

    with pytest.raises(StorageSecurityError):
        storage.make_dir("", "../forbidden")

    with pytest.raises(StorageSecurityError):
        storage.save("../", "hack.sh", io.BytesIO(b"rm -rf /"))

    with pytest.raises(StorageSecurityError):
        storage.open("../../etc/passwd")
