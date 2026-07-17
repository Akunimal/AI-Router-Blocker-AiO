# -*- coding: utf-8 -*-
import datetime
import os
import threading

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from ai_blocker.config import get_config_path


def get_cert_dir():
    base_dir = os.path.dirname(get_config_path())
    cert_dir = os.path.join(base_dir, "certs")
    os.makedirs(cert_dir, exist_ok=True)
    return cert_dir

def get_root_ca_paths():
    cert_dir = get_cert_dir()
    ca_cert_path = os.path.join(cert_dir, "codegate_root_ca.crt")
    ca_key_path = os.path.join(cert_dir, "codegate_root_ca.key")
    return ca_cert_path, ca_key_path

def generate_root_ca():
    ca_cert_path, ca_key_path = get_root_ca_paths()

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Generate CA certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"AI CodeGate"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"CodeGate Local Root CA"),
    ])

    now = datetime.datetime.utcnow()
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now - datetime.timedelta(days=1)
    ).not_valid_after(
        now + datetime.timedelta(days=3650)  # Valid for 10 years
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True
    ).sign(private_key, hashes.SHA256())

    # Write key to disk
    with open(ca_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Write cert to disk
    with open(ca_cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return ca_cert_path, ca_key_path

def get_or_create_root_ca():
    ca_cert_path, ca_key_path = get_root_ca_paths()
    if not os.path.exists(ca_cert_path) or not os.path.exists(ca_key_path):
        return generate_root_ca()
    return ca_cert_path, ca_key_path

def generate_leaf_cert(domain: str):
    """
    Generates a leaf certificate for the specified domain, signed by the Root CA.
    Returns the path to a temporary file containing both the private key and the certificate,
    which is often required by SSL contexts.
    """
    ca_cert_path, ca_key_path = get_or_create_root_ca()

    with open(ca_key_path, "rb") as f:
        ca_private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    with open(ca_cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    # Generate leaf key
    leaf_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, str(domain)),
    ])

    now = datetime.datetime.utcnow()
    builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        leaf_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now - datetime.timedelta(days=1)
    ).not_valid_after(
        now + datetime.timedelta(days=30)  # Short lived
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(str(domain))]),
        critical=False,
    )

    leaf_cert = builder.sign(ca_private_key, hashes.SHA256())  # type: ignore[arg-type]

    # Save to a domain-specific file
    cert_dir = get_cert_dir()
    domain_safe = domain.replace("*", "_wildcard_")
    leaf_path = os.path.join(cert_dir, f"{domain_safe}.pem")

    with open(leaf_path, "wb") as f:
        # Write private key
        f.write(leaf_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
        # Write leaf cert
        f.write(leaf_cert.public_bytes(serialization.Encoding.PEM))
        # Write CA cert chain
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    return leaf_path


# ?=??=? Leaf certificate cache ?=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=?

_leaf_cache: dict[str, str] = {}
_leaf_cache_lock = threading.Lock()


def get_or_generate_leaf_cert(domain: str) -> str:
    """Return a cached leaf certificate path, generating one if needed."""
    with _leaf_cache_lock:
        cached = _leaf_cache.get(domain)
        if cached and os.path.exists(cached):
            return cached
        path = generate_leaf_cert(domain)
        _leaf_cache[domain] = path
        return path


def clear_leaf_cache() -> None:
    """Clear the in-memory leaf certificate cache."""
    with _leaf_cache_lock:
        _leaf_cache.clear()


# ?=??=? OS Trust Store management ?=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=?

def is_root_ca_installed() -> bool:
    """Check if the CodeGate Root CA is installed in the OS trust store."""
    import platform
    import subprocess

    ca_cert_path, _ = get_root_ca_paths()
    if not os.path.exists(ca_cert_path):
        return False

    current_os = platform.system()
    try:
        if current_os == "Windows":
            result = subprocess.run(
                ["certutil", "-verifystore", "-user", "Root", "CodeGate Local Root CA"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        elif current_os == "Darwin":
            result = subprocess.run(
                ["security", "find-certificate", "-c", "CodeGate Local Root CA",
                 "/Library/Keychains/System.keychain"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        else:
            # Linux: check if our cert exists in the ca-certificates directory
            dest = "/usr/local/share/ca-certificates/codegate_root_ca.crt"
            return os.path.exists(dest)
    except Exception:
        return False


def uninstall_root_ca() -> bool:
    """Remove the CodeGate Root CA from the OS trust store."""
    import platform
    import subprocess

    current_os = platform.system()
    try:
        if current_os == "Windows":
            subprocess.run(
                ["certutil", "-delstore", "-user", "Root", "CodeGate Local Root CA"],
                capture_output=True, text=True, check=True
            )
        elif current_os == "Darwin":
            ca_cert_path, _ = get_root_ca_paths()
            subprocess.run(
                ["security", "remove-trusted-cert", "-d", ca_cert_path],
                capture_output=True, text=True, check=True
            )
        else:
            dest = "/usr/local/share/ca-certificates/codegate_root_ca.crt"
            if os.path.exists(dest):
                os.remove(dest)
                subprocess.run(
                    ["update-ca-certificates", "--fresh"],
                    capture_output=True, text=True, check=True
                )
        return True
    except Exception:
        return False

