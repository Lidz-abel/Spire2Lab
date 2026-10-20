"""Source pinning rejects drift and extra code before a build uses it."""

import hashlib
import io
import tarfile

import pytest
from sts2lab.source_integrity import verify_source_tree


def make_archive(tmp_path):
    archive = tmp_path / "pinned.tar.gz"
    content = b"public class Verified {}\n"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("root/src/Engine.cs")
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))
    tree = tmp_path / "vendor"
    (tree / "src").mkdir(parents=True)
    (tree / "src/Engine.cs").write_bytes(content)
    manifest = {
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "repository": "unit-test-fixture",
        "commit": "fixture",
    }
    return manifest, tree, archive


def test_valid_pin_allows_build_outputs_but_rejects_extra_sources(tmp_path):
    manifest, tree, archive = make_archive(tmp_path)
    (tree / "src/obj").mkdir()
    (tree / "src/obj/generated.cs").write_text("generated output")
    assert verify_source_tree(manifest, tree, archive)["verified_files"] == 1
    (tree / "src/Injected.cs").write_text("public class Unpinned {}")
    with pytest.raises(ValueError, match="Unexpected build source"):
        verify_source_tree(manifest, tree, archive)


def test_modified_or_missing_upstream_file_is_not_preserved_silently(tmp_path):
    manifest, tree, archive = make_archive(tmp_path)
    (tree / "src/Engine.cs").write_text("different mechanics")
    with pytest.raises(ValueError, match="differs from archive"):
        verify_source_tree(manifest, tree, archive)
    (tree / "src/Engine.cs").unlink()
    with pytest.raises(ValueError, match="Missing or unsafe"):
        verify_source_tree(manifest, tree, archive)


def test_archive_and_symlink_are_checked_before_use(tmp_path):
    manifest, tree, archive = make_archive(tmp_path)
    with pytest.raises(ValueError, match="checksum"):
        verify_source_tree({**manifest, "archive_sha256": "0" * 64}, tree, archive)
    (tree / "src/Engine.cs").unlink()
    (tree / "src/Engine.cs").symlink_to(archive)
    with pytest.raises(ValueError, match="Missing or unsafe"):
        verify_source_tree(manifest, tree, archive)
