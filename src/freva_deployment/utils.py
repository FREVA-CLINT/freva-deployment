"""Collection of utils for deployment."""
from __future__ import annotations
from getpass import getpass
import logging
from pathlib import Path
import re
import os
import shlex
from subprocess import run, PIPE
from tempfile import NamedTemporaryFile, TemporaryDirectory
import toml
from typing import Union

import appdirs
import nextcloud_client

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("freva-deployment")

config_dir = Path(appdirs.user_config_dir()) / "freva" / "deployment"
asset_dir = Path(appdirs.user_data_dir()) / "freva" / "deployment"
password_prompt = (
    "Set a master password, this password will be used to create\n"
    "a self signed certificate for accessing the freva credentials "
    "as mysql root password.\n: "
)


def download_data_from_nextcloud(
    public_url: str = "https://nextcloud.dkrz.de/s",
) -> dict[str, dict[str, dict[str, Union[str, list[str]]]]]:
    """Download server information from public next cloud share."""
    token = "yas2RZHRDyiMaPj"
    public_link = public_url + "/" + token
    with NamedTemporaryFile(suffix=".json") as temp_f:
        nc = nextcloud_client.Client.from_public_link(public_link)
        try:
            nc.get_file("/servers.toml", temp_f.name)
        except nextcloud_client.HTTPResponseError:
            return {}
        with open(temp_f.name) as f_obj:
            return toml.load(f_obj)


def upload_data_to_nextcloud(
    project_name: str,
    server_info: dict[str, dict[str, Union[str, list[str]]]],
    public_url: str = "https://nextcloud.dkrz.de/s",
) -> None:
    """Upload server information to public nextcloud share.

    Parameters
    ----------
    project_name: str
        Name of the freva project
    server_info: dict[str, str]
        Server names for each deployed service
    public_url: str
        The public nextcloud url where the information is upladed to.
    """
    token = "yas2RZHRDyiMaPj"
    public_link = public_url + "/" + token
    server_data = download_data_from_nextcloud()
    for service, values in server_info.items():
        try:
            server_data[project_name][service] = values
        except KeyError:
            server_data[project_name] = {service: values}
    cwd = os.getcwd()
    with TemporaryDirectory() as td:
        nc = nextcloud_client.Client.from_public_link(public_link)
        os.chdir(td)
        with open("servers.toml", "w") as f_obj:
            toml.dump(server_data, f_obj)
        try:
            success = nc.drop_file("servers.toml")
        except nextcloud_client.HTTPResponseError as e:
            logger.error("Could not upload server data to %s", public_link)
        finally:
            os.chdir(cwd)
        if success:
            logger.info("Server information updated at %s", public_url)


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
    msg = ""
    while True:
        try:
            return _create_passwd(min_characters, msg)
        except ValueError as e:
            msg = e.__str__() + " Re-enter password\n:"


def _create_passwd(min_characters: int, msg: str = "") -> str:
    """Create passwords."""
    master_pass = getpass(msg or password_prompt)
    is_ok = len(master_pass) > min_characters
    for check in ("[a-z]", "[A-Z]", "[0-9]"):
        if not re.search(check, master_pass):
            is_ok = False
            break
    is_ok *= len([True for c in "[_@$#$%^&*-!]" if c in master_pass]) > 0
    if not is_ok:
        raise ValueError(
            (
                f"Password must be at least {min_characters} characters long, "
                "have alphanumeric characters, both, lower and upper case "
                "characters, as well as special characters."
            )
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
            (
                "Email Address (eg, e.g. server FQDN or YOUR name) "
                f'[{defaults["emailAddress"]}]: '
            )
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
