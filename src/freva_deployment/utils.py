"""Collection of utils for deployment."""
from __future__ import annotations
import base64
from getpass import getpass
import hashlib
import logging
import json
from pathlib import Path
import re
import os
import shlex
from subprocess import run, PIPE
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import cast, NamedTuple

import appdirs
import nextcloud_client
import requests

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("freva-deployment")

config_dir = Path(appdirs.user_config_dir()) / "freva" / "deployment"
asset_dir = Path(appdirs.user_data_dir()) / "freva" / "deployment"
password_prompt = (
    "Set a master password, this password will be used to create\n"
    "a self signed certificate for accessing the freva credentials "
    "as mysql root password.\n: "
)

ServiceInfo = NamedTuple(
    "ServiceInfo", [("name", str), ("python_path", str), ("hosts", str)]
)


def get_setup_for_service(service: str, setups: list[ServiceInfo]) -> tuple[str, str]:
    """Get the setup of a service configuration."""
    for setup in setups:
        if setup.name == service:
            return setup.python_path, setup.hosts
    raise KeyError("Service not found")


def read_db_credentials(
    cert_file: Path, db_host: str, port: int = 5002
) -> dict[str, str]:
    """Read database config."""
    with cert_file.open() as f_obj:
        key = "".join([k.strip() for k in f_obj.readlines() if not k.startswith("-")])
        sha = hashlib.sha512(key.encode()).hexdigest()
    url = f"http://{db_host}:{port}/vault/data/{sha}"
    return requests.get(url).json()


def download_data_from_nextcloud(
    domain: str = "dkrz",
    public_url: str = "https://nextcloud.dkrz.de/s",
) -> dict[str, list[ServiceInfo]]:
    """Download server information from public next cloud share.

    Parameters
    ----------
    domain: str, default: dkrz
        Organization domain name where server information is stored.
    public_url:
        Url to the cloud storage object where the information is stored.

    Returns
    -------
    dict[str, list[NamedTuple("service", [("name", str), ("python_path", str),
                                     ("hosts", str)])]]
    """
    token = "yas2RZHRDyiMaPj"
    public_link = public_url + "/" + token
    with NamedTemporaryFile(suffix=".json") as temp_f:
        next_c = nextcloud_client.Client.from_public_link(public_link)
        try:
            next_c.get_file(f"/servers.{domain}", temp_f.name)
        except nextcloud_client.HTTPResponseError:
            return {}
        with open(temp_f.name, "rb") as f_obj:
            config = json.loads(base64.b64decode(f_obj.read()).decode())
    info: dict[str, list[ServiceInfo]] = {}
    for proj, _conf in config.items():
        info[cast(str, proj)] = [ServiceInfo(name=s, **c) for (s, c) in _conf.items()]
    return info


def upload_data_to_nextcloud(
    project_name: str,
    deployment_setup: dict[str, dict[str, str]],
    domain: str = "dkrz",
    public_url: str = "https://nextcloud.dkrz.de/s",
) -> None:
    """Upload server information to public nextcloud share.

    Parameters
    ----------
    project_name: str
        Name of the freva project
    deployment_setup: dict[str, str]
        Server names for each deployed service
    domain: str, deault: drkz
        Organization domain name where server information is stored.
    public_url: str
        The public nextcloud url where the information is upladed to.
    """
    token = "yas2RZHRDyiMaPj"
    public_link = public_url + "/" + token
    server_data = download_data_from_nextcloud(domain)
    _upload_data: dict[str, dict[str, dict[str, str]]] = {}
    for project, services in server_data.items():
        _upload_data[project] = {}
        for serv in services:
            _upload_data[project][serv.name] = dict(
                hosts=serv.hosts, python_path=serv.python_path
            )
    for service, config in deployment_setup.items():
        try:
            _upload_data[project_name][service] = config
        except KeyError:
            _upload_data[project_name] = {service: config}
    cwd = os.getcwd()
    with TemporaryDirectory() as temp_dir:
        next_c = nextcloud_client.Client.from_public_link(public_link)
        os.chdir(temp_dir)
        with open(f"servers.{domain}", "wb") as f_obj:
            f_obj.write(base64.b64encode(json.dumps(_upload_data).encode()))
        try:
            success = next_c.drop_file(f"servers.{domain}")
        except nextcloud_client.HTTPResponseError:
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
    is_ok: bool = len(master_pass) > min_characters
    for check in ("[a-z]", "[A-Z]", "[0-9]"):
        if not re.search(check, master_pass):
            is_ok = False
            break
    is_safe: bool = len([True for c in "[_@$#$%^&*-!]" if c in master_pass]) > 0
    if (is_ok * is_safe) is False:
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


def create_self_signed_cert(certfile: Path | str) -> Path:
    """Create a public and private key file.

    Parameters:
    ===========
    certfile:
        path of the certificate file.

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
