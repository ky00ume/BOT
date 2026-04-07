"""utils/assets.py — 에셋 무결성 검증 테스트."""

from pathlib import Path

import pytest

from utils import assets as assets_module
from utils.assets import REQUIRED_ASSETS, find_missing_assets, verify_assets


class TestRequiredAssetsPresent:
    """레포에 실제 커밋된 필수 에셋이 모두 존재해야 한다."""

    def test_required_assets_exist(self):
        missing = find_missing_assets()
        assert missing == [], f"필수 에셋 누락: {missing}"

    def test_verify_assets_passes(self):
        # 예외가 발생하지 않아야 한다.
        verify_assets()


class TestVerifyAssetsWithCustomList:
    def test_missing_raises_filenotfound(self, tmp_path):
        fake = tmp_path / "definitely_not_there.otf"
        with pytest.raises(FileNotFoundError):
            verify_assets([fake])

    def test_existing_file_passes(self, tmp_path):
        existing = tmp_path / "present.otf"
        existing.write_bytes(b"fake")
        verify_assets([existing])

    def test_find_missing_returns_only_missing(self, tmp_path):
        present = tmp_path / "a.bin"
        present.write_bytes(b"x")
        absent = tmp_path / "b.bin"
        missing = find_missing_assets([present, absent])
        assert missing == [absent]


class TestStaticDirPath:
    def test_static_dir_points_to_repo_static(self):
        expected = Path(assets_module.__file__).resolve().parent.parent / "static"
        assert assets_module.STATIC_DIR == expected

    def test_all_required_under_static_dir(self):
        for path in REQUIRED_ASSETS:
            assert str(path).startswith(str(assets_module.STATIC_DIR))
