#!/usr/bin/python3

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from json import dumps
from pathlib import Path
import sys
from subprocess import run, PIPE, Popen
import shlex
import time
import os
import hashlib
from functools import cached_property
import requests

app = Flask(__name__)
api = Api(app)
KEY_FILE = Path("/vault/keys")
CERT_DIR = Path("/data")


def read_key():
    unseal_keys = []
    token = ""
    with KEY_FILE.open("r") as f:
        for line in f.readlines():
            if "unseal key" in line.lower():
                unseal_keys.append(line.split(":")[-1].strip())
            if "initial root token" in line.lower():
                token = line.split(":")[-1].strip()
    return unseal_keys, token


def unseal():

    env = os.environ.copy()
    env["VAULT_ADDR"] = "http://127.0.0.1:8200"
    env["VAULT_SKIP_VERIFY"] = "true"
    unseal_keys, _ = read_key()
    for key in unseal_keys[:3]:
        run(shlex.split(f"vault operator unseal {key}"), env=env)


def deploy_vault():

    cmd = shlex.split("vault operator init")
    env = os.environ.copy()
    env["VAULT_ADDR"] = "http://127.0.0.1:8200"
    env["VAULT_SKIP_VERIFY"] = "true"
    res = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    with KEY_FILE.open("w") as f:
        f.write(res.stdout.decode())
    unseal_keys, token = read_key()
    unseal()
    if token:
        run(shlex.split(f"vault login {token}"), env=env)
        run(shlex.split(f"vault secrets enable -version=2 -path=kv kv"), env=env)
        run(
            shlex.split(f"vault policy write read-eval /vault/policy-file.hcl"), env=env
        )


class Vault(Resource):
    @staticmethod
    def _read_key(suffix):
        with (CERT_DIR / f"freva.{suffix}").open() as f:
            key = [k.strip() for k in f.readlines() if not k.startswith("-")]
        return ("".join(key)).encode()

    @cached_property
    def public_key(self):
        return hashlib.sha512(self._read_key("crt")).hexdigest()

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
        out, status = {}, 401
        if public_key != os.environ["ROOT_PW"]:
            return out, status
        _, token = read_key()
        # Get the information from the vault
        url = f"http://127.0.0.1:8200/v1/kv/data/read-eval"
        headers = {"X-Vault-Token": token}
        out = requests.get(url, headers=headers).json()["data"]
        out["data"]["db.passwd"] = entry
        r = requests.post(url, json=out, headers=headers)
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
        status = 401
        _, token = read_key()
        if public_key != self.public_key:
            return out, 401
        if entry == "token":
            return {"X-Vault-Token": token}, 200
        if entry == "data":
            # Get the information from the vault
            req = requests.get(
                "http://127.0.0.1:8200/v1/kv/data/read-eval",
                headers={"X-Vault-Token": token},
            )
        else:
            req = requests.get(
                f"http://127.0.0.1:8200/v1/kv/data/{entry}",
                headers={"X-Vault-Token": token},
            )
            out = req.json()["data"]["data"]
            status = req.status_code
        try:
            out = req.json()["data"]["data"]
            status = req.status_code
        except KeyError:
            out = req.json()
        return out, status


api.add_resource(Vault, "/vault/<entry>/<public_key>")  # Route_3

if __name__ == "__main__":
    try:
        cmd = sys.argv[1:]
    except IndexError:
        cmd = ["vault", "server", "-config", "/vault/vault-server-tls.hcl"]
    if len(cmd) == 0:
        cmd = ["vault", "server", "-config", "/vault/vault-server-tls.hcl"]
    p = Popen(cmd, env=os.environ.copy())
    time.sleep(1)
    if not KEY_FILE.exists():
        deploy_vault()
    else:
        unseal()
    app.run(host="0.0.0.0", port="5002")
    p.wait()
