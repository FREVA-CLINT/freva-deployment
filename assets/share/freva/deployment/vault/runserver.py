#!/usr/bin/python3

import base64
import binascii
import json
import logging
import os
from pathlib import Path
import random
from subprocess import Popen, PIPE, run
import shlex
import time
import threading
from typing import Any, Literal, List, Optional, TypedDict, cast

from flask import Flask
from flask_restful import Resource, Api
import requests

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

app = Flask("secret-reader")
api = Api(app)
logging.basicConfig(
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger("secret-reader")
app.logger = logger


def interact_with_vault(
    endpoint: str,
    method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
    loglevel: int = logging.ERROR,
    **kwargs: Any,
) -> Optional[requests.Response]:
    """Interact with the vault rest api.

    Parameters
    ---------
    url: str
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
                return response
            break
        except requests.exceptions.ConnectionError:
            logger.critical("Vault not active: sleeping for 1 second")
            time.sleep(1)
    logger.log(loglevel, text)
    return None


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


def unseal(auth: KeyType):
    """Open the vault.

    Parameters
    ----------
    auth: dict
        Dictionary holding the unseal keys and login token
    """
    for key in auth["keys"]:
        response = interact_with_vault(
            f"v1/sys/unseal", "PUT", json={"key": key}
        )
        data = response.json()
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
    interact_with_vault(f"v1/sys/health", "GET", headers=auth_header)
    interact_with_vault(
        f"v1/sys/mounts/kv",
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
        f"v1/sys/policies/acl/read-eval",
        "PUT",
        loglevel=logging.WARNING,
        headers=auth_header,
        json={"policy": policy_content},
    )


def deploy_vault():
    """Deploy a new vault if it hasn't been deployed yet."""
    auth = read_key()
    if not auth["keys"]:
        response = interact_with_vault(
            f"v1/sys/init",
            "PUT",
            headers={"Content-Type": "application/json"},
            json={
                "secret_shares": 5,  # Total number of share keys
                "secret_threshold": 3,  # Number of keys required to unseal
            },
        )
        data = response.json()
        auth["keys"] = data.get("keys", [])
        auth["token"] = data.get("token", "")
        KEY_FILE.write_bytes(
            base64.b64encode(json.dumps(auth).encode("utf-8"))
        )
    unseal(auth)


class Vault(Resource):
    _token: str = ""

    @property
    def token(self) -> str:
        """Get the vault login token."""
        if not self._token:
            with ThreadLock:
                self._token = read_key()["token"]
        return self._token

    def post(self, entry, public_key):
        """Post method, for setting a new db_password.

        Parameters:
        -----------
        entry: str
            the new database password
        public_key: str
            mysql root password to

        Returns:
        --------
            dict: status information
        """
        out, status = {}, 400
        if public_key != os.environ["ROOT_PW"]:
            return out, status
        # Get the information from the vault
        url = f"http://127.0.0.1:8200/v1/kv/data/read-eval"
        headers = {"X-Vault-Token": self.token}
        out = (
            requests.get(url, headers=headers, timeout=3)
            .json()
            .get("data", {})
        )
        try:
            out["data"]["db.passwd"] = entry
        except KeyError:
            pass
        _ = requests.post(url, json=out, headers=headers)
        return {}, 201

    def get(self, entry, public_key):
        """Get method, for getting vault information.

        Parameters:
        -----------
        entry: str
            the kind of inormation that is returned, can be
            key#N : to get the unseal key #N
            token: to get the login token
            data: to get the key-value data that is stored in the vault
        public_key: hashlib.sha512
            hexdigest representation of the sha512 public key that is stored
            on the docker container.

        Returns:
        --------
            dict: Vault information
        """
        out = {}
        status = 400
        if len(public_key) != 128:  # This is not a checksum of a cert.
            is_sealed = getattr(
                interact_with_vault(f"v1/sys/seal-status"), "json", lambda: {}
            )().get("sealed", True)
            vault_status = {True: "sealdd", False: "unsealed"}[is_sealed]
            text = f"But the vault is {vault_status}"
            return f"{random.choice(PHRASES)} {text}", status
        if entry == "data":
            # Get the information from the vault
            req = interact_with_vault(
                f"v1/kv/data/read-eval",
                headers={"X-Vault-Token": self.token},
            )
        else:
            req = interact_with_vault(
                f"v1/kv/data/{entry}",
                headers={"X-Vault-Token": self.token},
            )
        try:
            out = req.json()["data"]["data"]
            status = req.status_code
        except KeyError:
            out = req.json()
            status = req.status_code
        except (json.JSONDecodeError, AttributeError):
            out = {}
        return out, status


api.add_resource(Vault, "/vault/<entry>/<public_key>")  # Route_3

if __name__ == "__main__":
    Popen(["vault", "server", "-config", "/vault/vault-server-tls.hcl"])
    deploy_vault()
