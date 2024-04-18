"""Generate keys."""

import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

_CRYPTO = True
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
except ImportError:
    _CRYPTO = False


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
        self._private_key: Optional["rsa.RSAPrivateKey"] = None
        self._temp_dir = TemporaryDirectory("random_keys")

    def _check_crypto(self) -> None:
        if not _CRYPTO:
            raise ImportError(
                "Please install the `cryptography` python module."
                " in order to generate certificates."
            )

    @property
    def private_key(self) -> "rsa.RSAPrivateKey":
        if self._private_key is not None:
            return self._private_key
        self._private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        return self._private_key

    @property
    def private_key_pem(self) -> bytes:
        """Create a new private key pem if it doesn't exist."""
        self._check_crypto()
        if self._private_key_pem is None:
            self._private_key_pem = self.private_key.private_bytes(
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
        self._check_crypto()
        if self._public_key_pem is None:
            public_key = self.private_key.public_key()
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
        self._check_crypto()
        temp_file = (Path(self._temp_dir.name) / self.base_name).with_suffix(".key")
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
        temp_file = (Path(self._temp_dir.name) / self.base_name).with_suffix(".pem")
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
        temp_file = (Path(self._temp_dir.name) / self.base_name).with_suffix(".crt")
        if not temp_file.is_file():
            temp_file.write_bytes(self.certificate_chain)
        return str(temp_file)

    def create_self_signed_cert(self) -> "x509.Certificate":
        """
        Create a self-signed certificate using the public key.

        Returns
        -------
            x509.Certificate: The self-signed certificate.
        """
        self._check_crypto()
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, self.common_name)])
            )
            .sign(self.private_key, hashes.SHA256(), default_backend())
        )

        certificate = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(csr.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.UTC))
            .not_valid_after(
                datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
            )
            .sign(self.private_key, hashes.SHA256(), default_backend())
        )

        return certificate

    @property
    def certificate_chain(self) -> bytes:
        """The certificate chain."""
        certificate = self.create_self_signed_cert()
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)
        return self.public_key_pem + certificate_pem


if __name__ == "__main__":
    # Create an instance of RandomKeys
    keys = RandomKeys()

    # Output the public key
    print("Public Key:")
    print(Path(keys.private_key_file).read_text())
    # Output the certificate chain
    print("\nPublic Key:")
    print(Path(keys.public_chain_file).read_text())
