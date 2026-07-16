import os
import shutil
import tempfile

import pytest

pytest.importorskip("cryptography")

from ai_blocker import tls_manager


def test_get_cert_dir(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        cert_dir = tls_manager.get_cert_dir()
        assert os.path.exists(cert_dir)
        assert cert_dir.endswith("certs")
    finally:
        shutil.rmtree(temp_dir)


def test_get_root_ca_paths(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        ca_cert_path, ca_key_path = tls_manager.get_root_ca_paths()
        assert ca_cert_path.endswith("ai_devsec_root_ca.crt")
        assert ca_key_path.endswith("ai_devsec_root_ca.key")
        assert os.path.dirname(ca_cert_path) == os.path.dirname(ca_key_path)
    finally:
        shutil.rmtree(temp_dir)


def test_generate_root_ca(mocker):
    from cryptography.x509 import load_pem_x509_certificate
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        ca_cert, ca_key = tls_manager.generate_root_ca()
        assert os.path.exists(ca_cert)
        assert os.path.exists(ca_key)
        with open(ca_cert, "rb") as f:
            cert = load_pem_x509_certificate(f.read())
            assert cert.subject.get_attributes_for_oid(tls_manager.NameOID.COMMON_NAME)[0].value == "AI DevSec Local Root CA"
    finally:
        shutil.rmtree(temp_dir)


def test_get_or_create_root_ca(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        ca_cert, ca_key = tls_manager.get_or_create_root_ca()
        assert os.path.exists(ca_cert)
        assert os.path.exists(ca_key)
        cert_mtime = os.path.getmtime(ca_cert)
        ca_cert2, ca_key2 = tls_manager.get_or_create_root_ca()
        assert ca_cert == ca_cert2
        assert ca_key == ca_key2
        assert os.path.getmtime(ca_cert) == cert_mtime
    finally:
        shutil.rmtree(temp_dir)


def test_generate_leaf_cert(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        leaf_path = tls_manager.generate_leaf_cert("test.domain.com")
        assert os.path.exists(leaf_path)
        assert "test.domain.com" in leaf_path
    finally:
        shutil.rmtree(temp_dir)


def test_generate_leaf_cert_wildcard_domain(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        leaf_path = tls_manager.generate_leaf_cert("*.example.com")
        assert os.path.exists(leaf_path)
        assert "_wildcard_" in leaf_path
    finally:
        shutil.rmtree(temp_dir)


def test_get_or_generate_leaf_cert_cache(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        path1 = tls_manager.get_or_generate_leaf_cert("cached.domain.com")
        assert os.path.exists(path1)
        path2 = tls_manager.get_or_generate_leaf_cert("cached.domain.com")
        assert path1 == path2
        path3 = tls_manager.get_or_generate_leaf_cert("other.domain.com")
        assert path3 != path1
    finally:
        shutil.rmtree(temp_dir)


def test_get_or_generate_leaf_cert_cache_miss_on_deleted_file(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        path = tls_manager.get_or_generate_leaf_cert("evict.me")
        assert os.path.exists(path)
        os.remove(path)
        path2 = tls_manager.get_or_generate_leaf_cert("evict.me")
        assert os.path.exists(path2)
    finally:
        shutil.rmtree(temp_dir)


def test_clear_leaf_cache(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        tls_manager.get_or_generate_leaf_cert("clear.test")
        tls_manager.clear_leaf_cache()
        path = tls_manager.get_or_generate_leaf_cert("clear.test")
        assert os.path.exists(path)
    finally:
        shutil.rmtree(temp_dir)


def test_is_root_ca_installed_no_cert_file(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        assert tls_manager.is_root_ca_installed() is False
    finally:
        shutil.rmtree(temp_dir)


def test_is_root_ca_installed_windows(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        tls_manager.generate_root_ca()
        mocker.patch("platform.system", return_value="Windows")
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        assert tls_manager.is_root_ca_installed() is True
        mock_run.assert_called_once()
        mock_run.return_value.returncode = 1
        assert tls_manager.is_root_ca_installed() is False
    finally:
        shutil.rmtree(temp_dir)


def test_is_root_ca_installed_macos(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        tls_manager.generate_root_ca()
        mocker.patch("platform.system", return_value="Darwin")
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        assert tls_manager.is_root_ca_installed() is True
    finally:
        shutil.rmtree(temp_dir)


def test_is_root_ca_installed_linux(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        tls_manager.generate_root_ca()
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch("os.path.exists", return_value=True)
        assert tls_manager.is_root_ca_installed() is True
        mocker.patch("os.path.exists", return_value=False)
        assert tls_manager.is_root_ca_installed() is False
    finally:
        shutil.rmtree(temp_dir)


def test_uninstall_root_ca_windows(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        tls_manager.generate_root_ca()
        mocker.patch("platform.system", return_value="Windows")
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        assert tls_manager.uninstall_root_ca() is True
    finally:
        shutil.rmtree(temp_dir)


def test_uninstall_root_ca_failure_returns_false(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)
        tls_manager.generate_root_ca()
        mocker.patch("platform.system", return_value="Windows")
        mocker.patch("subprocess.run", side_effect=Exception("certutil not found"))
        assert tls_manager.uninstall_root_ca() is False
    finally:
        shutil.rmtree(temp_dir)
