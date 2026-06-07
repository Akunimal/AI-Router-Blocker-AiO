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

def test_generate_root_ca(mocker):
    temp_dir = tempfile.mkdtemp()
    try:
        mock_config_path = os.path.join(temp_dir, "AI-Blocker", "config.json")
        mocker.patch("ai_blocker.tls_manager.get_config_path", return_value=mock_config_path)

        ca_cert, ca_key = tls_manager.generate_root_ca()
        assert os.path.exists(ca_cert)
        assert os.path.exists(ca_key)

        # Check they load without error
        from cryptography.x509 import load_pem_x509_certificate
        with open(ca_cert, "rb") as f:
            cert = load_pem_x509_certificate(f.read())
            assert cert.subject.get_attributes_for_oid(tls_manager.NameOID.COMMON_NAME)[0].value == "AI DevSec Local Root CA"
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
