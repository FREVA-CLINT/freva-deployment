"""Collection of utils for deployment."""
from __future__ import annotations
import appdirs
from getpass import getpass
import logging
from pathlib import Path
import re
import shlex
from subprocess import run, PIPE

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("freva-deployment")

config_dir = Path(appdirs.user_config_dir()) / "freva" / "deployment"
asset_dir = Path(appdirs.user_data_dir()) / "freva" / "deployment"
password_prompt = ("Set a master password, this password will be used to create\n"
                   "a self signed certificate for accessing the freva credentials "
                   "as mysql root password.\n: ")


def get_passwd(min_characters: int = 8) -> str:
    """Create a secure pasword.

    Parameters:
    ===========
    min_characters:
        The minimum lenght of the password (default 8)

    Returns:
    ========
    str: The password
    """
    logger.info("Creating Password")
    while True:
        try:
            return _create_passwd(min_characters)
        except ValueError as e:
            logger.error(e.__str__())


def _create_passwd(min_characters: int) -> str:
    """Create passwords."""
    master_pass = getpass(password_prompt)
    is_ok = len(master_pass) > min_characters
    for check in ("[a-z]", "[A-Z]", "[0-9]"):
        if not re.search(check, master_pass):
            is_ok = False
            break
    is_ok *= len([True for c in "[_@$#$%^&*-!]" if c in master_pass]) > 0
    if not is_ok:
        raise ValueError(
            (f"Password must be at least {min_characters} characters long, "
             "have alphanumeric characters, both, lower and upper case "
             "characters, as well as special characters.")
        )
    master_pass_2 = getpass("Re enter master password\n: ")
    if master_pass != master_pass_2:
        raise ValueError("Passwords do not match")
    return master_pass


def create_self_signed_cert(certfile: Path | str, overwrite: bool = True) -> Path:
    """Create a public and private key file.

    Parameters:
    ===========
    certfile:
        path of the certificate file.
    overwrite:
        overwrite any existing certificate files.

    Returns:
    ========
    pathlib.Path : path to the public certificate file.

    """
    public_cert = Path(certfile).with_suffix(".crt")
    private_cert = public_cert.with_suffix(".key")
    public_cert.parent.mkdir(exist_ok=True, parents=True)
    logger.info(f"Creating Self Signed Certificate file: {public_cert}")
    msg = """You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank."""
    print(msg)
    for file in private_cert, public_cert:
        try:
            file.unlink()
        except FileNotFoundError:
            pass
    defaults = dict(
        C="DE",
        ST="Hamburg",
        L="Hamburg",
        O="Deutsches Klimarechenzentrum GmbH",
        OU="DM",
        CN="freva.dkrz.de",
        emailAddress="freva@dkrz.de",
    )
    steps = dict(
        C=input(f'Country Name (2 letter code) [{defaults["C"]}]: '),
        ST=input(f'State or Province Name (full name) [{defaults["ST"]}]: '),
        L=input(f'Locality Name (eg, city) [{defaults["L"]}]: '),
        O=input(f'Organization Name (eg, company) [{defaults["O"]}]: '),
        OU=input(f'Organization Unit Name (eg, section) [{defaults["OU"]}]: '),
        CN=input(
            f'Common Name (eg, e.g. server FQDN or YOUR name) [{defaults["CN"]}]: '
        ),
        emailAddress=input(
            ("Email Address (eg, e.g. server FQDN or YOUR name) "
             f'[{defaults["emailAddress"]}]: ')
        ),
    )
    sub_j = "/".join(f"{k}={v.strip() or defaults[k]}" for (k, v) in steps.items())
    cmd = (
        f"openssl req -newkey rsa:4096 -x509 -sha256 -nodes -out {public_cert}"
        f' -keyout {private_cert} -subj "/{sub_j} "'
    )
    run(shlex.split(cmd), stdout=PIPE, stderr=PIPE, check=False)
    for file in private_cert, public_cert:
        if not file.is_file():
            raise FileNotFoundError(
                f"Certificate creation failed, check the command:\n {cmd}"
            )
    return public_cert.absolute()
