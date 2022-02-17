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
KEY_FILE = Path('/vault/keys')
CERT_DIR = Path('/mnt')

def unseal():

    env = os.environ.copy()
    env['VAULT_ADDR'] = 'http://127.0.0.1:8200'
    env['VAULT_SKIP_VERIFY'] = 'true'
    with KEY_FILE.open() as f:
        unseal_keys = []
        for line in f.readlines():
            if 'unseal ' in line.lower():
                unseal_keys.append(line.split(':')[-1].strip())
    for key in unseal_keys[:3]:
        run(shlex.split(f'vault operator unseal {key}'), env=env)



def deploy_vault():

    cmd = shlex.split('vault operator init')
    env = os.environ.copy()
    env['VAULT_ADDR'] = 'http://127.0.0.1:8200'
    env['VAULT_SKIP_VERIFY']='true'
    res = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    stdout = res.stdout.decode().split('\n')
    unseal_keys = []
    token = None
    print(res.stderr.decode())
    print('\n'.join(stdout))
    for line in stdout:
        if 'unseal key' in line.lower():
            unseal_keys.append(line.split(':')[-1].strip())
        if 'initial root token' in line.lower():
            token = line.split(':')[-1].strip()
            with KEY_FILE.open('w') as f:
                for nn, key in enumerate(unseal_keys):
                    f.write(f'Unseal key #{nn+1}: {key}\n')
                f.write(f'Root token: {token}')
    unseal()
    if token:
        run(shlex.split(f'vault login {token}'), env=env)
        run(shlex.split(f'vault secrets enable -version=2 -path=kv kv'), env=env)
        run(shlex.split(f'vault policy write read-eval /vault/policy-file.hcl'), env=env)



class Vault(Resource):

    @staticmethod
    def _read_key(suffix):
        with (CERT_DIR / f'freva.{suffix}').open() as f:
            key = [k.strip() for k in f.readlines() if not k.startswith('-')]
        return (''.join(key)).encode()

    @cached_property
    def private_key(self):
        return hashlib.sha512(self._read_key('key')).hexdigest()

    @cached_property
    def public_key(self):
        return hashlib.sha512(self._read_key('crt')).hexdigest()

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
        if public_key != os.environ['ROOT_PW']:
            return jsonify({'status':'fail'})
        token = self._get_keys('token', public_key, check=False)['key']
        # Get the information from the vault
        url = f'http://127.0.0.1:8200/v1/kv/data/read-eval'
        headers = {"X-Vault-Token": token}
        out = requests.get(url, headers=headers).json()['data']
        out['data']['db.passwd'] = entry
        r = requests.post(url, json=out, headers=headers)
        return jsonify({'status':'success'})
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


        if entry == 'data':
            token = self._get_keys('token', public_key)['key']
            # Get the information from the vault
            out = requests.get(f'http://127.0.0.1:8200/v1/kv/data/read-eval',
                        headers={"X-Vault-Token": token}).json()['data']['data']
        else:
            out = self._get_keys(entry, public_key)
        return jsonify(out)

    def _get_keys(self, entry, public_key, check=True):
        """Get vault server information."""
        entry = entry.strip().replace(' ','').replace('#','')
        if public_key != self.public_key and check:
            return jsonify({'key': None})
        with KEY_FILE.open() as f:
            for line in f.readlines():
                key, value = line.split(':')
                key = key.replace('Unseal ','').replace('Root ', '').replace(' ','').replace('#','')
                if key == entry:
                    return {'key': value.strip()}

api.add_resource(Vault, '/vault/<entry>/<public_key>') # Route_3

if __name__ == '__main__':
    try:
        cmd = sys.argv[1:]
    except IndexError:
        cmd = ['vault', 'server', '-config', '/vault/vault-server-tls.hcl']
    if len(cmd) == 0:
        cmd = ['vault', 'server', '-config', '/vault/vault-server-tls.hcl']
    p=Popen(cmd, env=os.environ.copy())
    time.sleep(0.5)
    if not KEY_FILE.is_file():
        deploy_vault()
    else:
        unseal()
    app.run(host='0.0.0.0', port='5002')
    p.wait()
