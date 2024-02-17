"""Generate keys."""

import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from cryptography.x509 import Name, NameAttribute


class RandomKeys:
    """Generate public and private server keys.

    Parameters:
        base_name (str): The path prefix for all key files.
        common_name (str): The common name for the certificate.
    """

    def __init__(
        self, base_name: str = "freva", common_name: str = "localhost"
    ) -> None:
        self.base_name = base_name
        self.common_name = common_name
        self._private_key_pem: Optional[bytes] = None
        self._public_key_pem: Optional[bytes] = None
        self._temp_dir = TemporaryDirectory("random_keys")

    @property
    def private_key_pem(self) -> bytes:
        """Create a new private key pem if it doesn't exist."""
        if self._private_key_pem is None:
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )

            self._private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        return self._private_key_pem

    @property
    def public_key_pem(self) -> bytes:
        """
        Generate a public key pair using RSA algorithm.

        Returns:
            bytes: The public key (PEM format).
        """
        if self._public_key_pem is None:
            private_key = serialization.load_pem_private_key(
                self.private_key_pem, password=None, backend=default_backend()
            )
            public_key = private_key.public_key()
            self._public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        return self._public_key_pem

    @property
    def private_key_file(self) -> str:
        """
        Save the private key to a file.

        Returns:
            str: The filename of the private key file.
        """
        temp_file = (Path(self._temp_dir.name) / self.base_name).with_suffix(
            ".key"
        )
        if not temp_file.is_file():
            temp_file.write_bytes(self.private_key_pem)
        return str(temp_file)

    @property
    def public_key_file(self) -> str:
        """
        Save the public key to a file.

        Returns:
            str: The filename of the public key file.
        """
        temp_file = (Path(self._temp_dir.name) / self.base_name).with_suffix(
            ".crt"
        )
        if not temp_file.is_file():
            temp_file.write_bytes(self.public_key_pem)
        return str(temp_file)

    @property
    def public_chain_file(self) -> str:
        """
        Save the public key and certificate chain to a file.

        Returns:
            str: The filename of the certificate chain file.
        """
        temp_file = (Path(self._temp_dir.name) / self.base_name).with_suffix(
            ".pem"
        )
        if not temp_file.is_file():
            temp_file.write_bytes(self.certificate_chain)
        return str(temp_file)

    def create_self_signed_cert(self) -> x509.Certificate:
        """
        Create a self-signed certificate using the public key.

        Returns
        -------
            x509.Certificate: The self-signed certificate.
        """
        private_key = serialization.load_pem_private_key(
            self.private_key_pem, password=None, backend=default_backend()
        )
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name(
                    [x509.NameAttribute(NameOID.COMMON_NAME, self.common_name)]
                )
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        certificate = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(csr.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        return certificate

    @property
    def certificate_chain(self) -> bytes:
        """The certificate chain."""
        certificate = self.create_self_signed_cert()
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)
        return self.public_key_pem + certificate_pem