"""Collection of utils for deployment."""
from __future__ import annotations
import hashlib
import logging
import json
from pathlib import Path
import re
import shlex
from subprocess import run, PIPE
from typing import cast, NamedTuple

import appdirs
import requests
from rich.console import Console
from rich.prompt import Prompt
import toml

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("freva-deployment")

RichConsole = Console(style="bold", markup=True, force_terminal=True)
config_dir = Path(appdirs.user_config_dir()) / "freva" / "deployment"
asset_dir = Path(appdirs.user_data_dir()) / "freva" / "deployment"
password_prompt = (
    "Choose a [b]master password[/], this password will be used to:\n"
    "- create a self signed [magenta]certificate[/] for accessing the freva credentials\n"
    "- create the [magenta]mysql root[/] password\n"
    "- set the [magenta]django admin[/] web password\n[b]enter master password[/]"
)

ServiceInfo = NamedTuple(
    "ServiceInfo", [("name", str), ("python_path", str), ("hosts", str)]
)


def guess_map_server(
    inp_server: str | None, default_port: int = 6111, mandatory: bool = True
) -> str:
    """Try to get the server name mapping the freva infrastructure.

    Parameters
    ----------
    inp_server: str | None
        Input server name, if None given, the code tries to read the
        the server name from a previous deployment setup.
    default_port: int, default: 6111
        The port to connect to
    mandatory: bool, default: True
        If mandatory is set and no server could be found an error is risen.

    Returns
    -------
    str: hostname of the server that runs the server map service

    Raises
    ------
    ValueError: If no server could be found a ValueError is raised.
    """
    inp_server = inp_server or ""
    if inp_server:
        host_name, _, port = inp_server.partition(":")
        port = port or str(default_port)
        return f"{host_name}:{port}"
    cache_dir = Path(appdirs.user_cache_dir()) / "freva-deployment"
    try:
        with (cache_dir / "freva_deployment.json").open() as f_obj:
            inp_server = cast(str, json.load(f_obj)["server_map"])
            host_name, _, port = inp_server.partition(":")
            port = port or str(default_port)
            return f"{host_name}:{port}"
    except (FileNotFoundError, IOError, ValueError, KeyError, json.JSONDecodeError):
        pass
    if mandatory:
        raise ValueError(
            "You have to set the hostname to the services mapping "
            "the freva infrastructure using the --server-map flag."
        )
    return ""


def set_log_level(verbosity: int) -> None:
    """Set the log level of the logger."""
    logger.setLevel(max(logging.INFO - 10 * verbosity, logging.DEBUG))


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


def download_server_map(
    server_map,
) -> dict[str, list[ServiceInfo]]:
    """Download server information from the service that stores the server arch.

    Parameters
    ----------
    server_map: str,
        The hostname holding the server archtiecture information.
    Returns
    -------
    dict[str, list[NamedTuple("service", [("name", str), ("python_path", str),
                                     ("hosts", str)])]]
    """
    info: dict[str, list[ServiceInfo]] = {}
    host, _, port = server_map.partition(":")
    port = port or "6111"
    req = requests.get(f"http://{host}:{port}")
    if req.status_code != 200:
        logger.error(req.json())
        return {}
    for proj, conf in req.json().items():
        info[cast(str, proj)] = [
            ServiceInfo(name=s, python_path=c[0], hosts=c[-1])
            for (s, c) in conf.items()
        ]
    return info


def upload_server_map(
    server_map: str,
    project_name: str,
    deployment_setup: dict[str, dict[str, str]],
) -> None:
    """Upload server information to service that stores server archtiecture.

    Parameters
    ----------
    server_map: str
        The hostname holding the server archtiecture information.
    project_name: str
        Name of the freva project
    deployment_setup: dict[str, str]
        Server names for each deployed service
    """
    _upload_data: dict[str, dict[str, str]] = {}
    for service, config in deployment_setup.items():
        _upload_data[service] = config
    host, _, port = server_map.partition(":")
    port = port or "6111"
    req_data = dict(config=toml.dumps(_upload_data))
    logger.debug("Uploading %s", req_data)
    req = requests.put(f"http://{host}:{port}/{project_name}", data=req_data)
    if req.status_code == 201:
        logger.info("Server information updated at %s", host)
    else:
        logger.error("Could not update server information %s", req.json())


def get_passwd(min_characters: int = 8) -> str:
    """Create a secure pasword.

    Parameters
    ==========
    min_characters:
        The minimum lenght of the password (default 8)

    Returns
    =======
    str: The password
    """
    logger.info("Creating Password")
    msg = ""
    RichConsole
    while True:
        try:
            return _create_passwd(min_characters, msg)
        except ValueError as e:
            RichConsole.print(f"[red]{e.__str__()}[/]")
            msg = "[b]re-enter[/] master password"


def _create_passwd(min_characters: int, msg: str = "") -> str:
    """Create passwords."""
    master_pass = Prompt.ask(msg or password_prompt, password=True)
    is_ok: bool = len(master_pass) > min_characters
    for check in ("[a-z]", "[A-Z]", "[0-9]"):
        if not re.search(check, master_pass):
            is_ok = False
            break
    is_safe: bool = len([True for c in "[_@$#$%^&*-!]" if c in master_pass]) > 0
    if is_ok is False or is_safe is False:
        raise ValueError(
            (
                "Password confirm the following constraints:\n"
                f"- {min_characters} alphanumeric characters long,\n"
                "- have both lower and upper case characters,\n"
                "- have at least one special special characters."
            )
        )
    master_pass_2 = Prompt.ask("[bold green]re-enter[/] master password", password=True)
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
