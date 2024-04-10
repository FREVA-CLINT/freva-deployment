#!/usr/bin/python3

import base64
import binascii
import json
import logging
import os
import random
import shlex
import threading
import time
from pathlib import Path
from subprocess import PIPE, Popen, run
from typing import Any, Dict, List, Literal, TypedDict, cast

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

KeyType = TypedDict("KeyType", {"keys": List[str], "token": str})
KEY_FILE = Path("/vault/file/keys")
CERT_DIR = Path("/data")
ThreadLock = threading.Lock()
VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
PHRASES = [
    "There seems to be a noose around this request.",
    "Our guns jammed! Something went wrong.",
    "When you have to shoot, shoot, don't talk.",
    "The bullets didn't fire.",
    "I've never seen so many men wasted so badly.",
    "You're not digging.",
    "We're in the desert without a horse.",
    "We faced a showdown, and it didn't end well."
    "Blondie! You know what you are? Just a dirty son of a...",
]
__version__ = "2023.10.1"

app = FastAPI(
    title="secret-reader",
    description="Read information from a vault",
    version=__version__,
)
logging.basicConfig(
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger("secret-reader")


class VaultCore:
    _token: str = ""

    @property
    def token(self) -> str:
        """Get the vault login token."""
        if not self._token:
            with ThreadLock:
                self._token = read_key()["token"]
        return self._token


Vault = VaultCore()


def interact_with_vault(
    endpoint: str,
    method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
    loglevel: int = logging.ERROR,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Interact with the vault rest api.

    Parameters
    ---------
    endpoint: str
        The vault endpoint.
    method: str, default: GET
        Use a GET, PUT or POST method
    loglevel: int, default: 40
        Which log level to emit if errors occur.
    kwargs:
        Additional arguments for the request.
    """
    text = f"Failed to connect to {endpoint}"
    for _ in range(10):
        try:
            response = requests.request(
                method, f"{VAULT_ADDR}/{endpoint}", **kwargs
            )
            text = response.text
            if response.status_code >= 200 and response.status_code < 300:
                return cast(Dict[str, Any], response.json())
            break
        except requests.exceptions.ConnectionError:
            logger.critical("Vault not active: sleeping for 1 second")
            time.sleep(1)
        except Exception as error:
            text = str(error)
            break
    logger.log(loglevel, text)
    return {}


def read_key() -> KeyType:
    """Read the login token and the vault seal keys from a secret file."""
    auth: KeyType = {"keys": [], "token": ""}
    try:
        return cast(
            KeyType, json.loads(base64.b64decode(KEY_FILE.read_bytes()))
        )
    except FileNotFoundError:
        return auth
    except (json.JSONDecodeError, binascii.Error):
        pass
    auth_content = KEY_FILE.read_text(encoding="utf-8")
    for line in auth_content.splitlines():
        if "unseal key" in line.lower():
            auth["keys"].append(line.split(":")[-1].strip())
        if "initial root token" in line.lower():
            auth["token"] = line.split(":")[-1].strip()
    KEY_FILE.write_bytes(base64.b64encode(json.dumps(auth).encode("utf-8")))
    return auth


def unseal(auth: KeyType) -> None:
    """Open the vault.

    Parameters
    ----------
    auth: dict
        Dictionary holding the unseal keys and login token
    """
    for key in auth["keys"]:
        data = interact_with_vault("v1/sys/unseal", "PUT", json={"key": key})
        if data.get("sealed", False) is False:
            logger.info("Vault has been successfully unsealed!")
            login(auth["token"])
            return
    logger.error(
        "Failed to unseal Vault. Please check the provided unseal keys and Vault status."
    )


def login(token: str) -> None:
    """Login to the vault and adjust the correct settings.

    Parameters
    ----------
    token: str
        The login token for the opened vault.
    """
    if not token:
        return
    auth_header = {"X-Vault-Token": token, "Content-Type": "application/json"}
    # Make vault commands possible and login from the cmd.
    run(shlex.split(f"vault login {token}"), stderr=PIPE, stdout=PIPE)
    interact_with_vault("v1/sys/health", "GET", headers=auth_header)
    interact_with_vault(
        "v1/sys/mounts/kv",
        "PUT",
        loglevel=logging.WARNING,
        headers=auth_header,
        json={"type": "kv", "options": {"version": "2"}},
    )
    try:
        policy_content = Path("/vault/policy-file.hcl").read_text()
    except (FileNotFoundError, PermissionError):
        return
    interact_with_vault(
        "v1/sys/policies/acl/read-eval",
        "PUT",
        loglevel=logging.WARNING,
        headers=auth_header,
        json={"policy": policy_content},
    )


def deploy_vault() -> None:
    """Deploy a new vault if it hasn't been deployed yet."""
    auth = read_key()
    if not auth["keys"]:
        data = interact_with_vault(
            "v1/sys/init",
            "PUT",
            headers={"Content-Type": "application/json"},
            json={
                "secret_shares": 5,  # Total number of share keys
                "secret_threshold": 3,  # Number of keys required to unseal
            },
        )
        auth["keys"] = data.get("keys", [])
        auth["token"] = data.get("token", data.get("root_token", ""))
        KEY_FILE.write_bytes(
            base64.b64encode(json.dumps(auth).encode("utf-8"))
        )
    unseal(auth)


@app.get("/vault/status")
async def get_vault_status() -> JSONResponse:
    """Get the status of the vault."""
    is_sealed = interact_with_vault("v1/sys/seal-status").get("sealed")
    vault_status = {True: "sealed", False: "unsealed", None: "down"}[is_sealed]
    return JSONResponse(content={"status": vault_status}, status_code=200)


@app.get("/vault/data/{public_key}")
async def read_secret(public_key: str) -> JSONResponse:
    """Read the secrets from the vault.

    Parameters
    ----------
    public_key: str
        hexdigest representation of the sha512 public key that is stored
        on the docker container.


    Returns
    -------
    dict: A key-value paired dictionary containing the secrets.
    """
    out = {}
    status = 400
    if len(public_key) != 128:  # This is not a checksum of a cert.
        is_sealed = interact_with_vault("v1/sys/seal-status").get("sealed")
        vault_status = {True: "sealed", False: "unsealed", None: "down"}[
            is_sealed
        ]
        text = f"But the vault is {vault_status}"
        raise HTTPException(
            detail=f"{random.choice(PHRASES)} {text}", status_code=status
        )
    # Get the information from the vault
    req = requests.get(
        f"{VAULT_ADDR}/v1/kv/data/read-eval",
        headers={"X-Vault-Token": Vault.token},
    )
    try:
        out = req.json().get("data", {}).get("data", {})
        status = req.status_code
    except (json.JSONDecodeError, AttributeError):
        out = {}
    return JSONResponse(content=out, status_code=status)


if __name__ == "__main__":
    Popen(["vault", "server", "-config", "/vault/vault-server-tls.hcl"])
    deploy_vault()
    Popen(
        [
            "vault",
            "policy",
            "write",
            "eval-policy",
            "/vault/policy-file.hcl",
        ]
    )
