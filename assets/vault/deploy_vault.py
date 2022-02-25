#!/usr/bin/python3

from subprocess import run, PIPE
import shlex
import os

if __name__ == "__main__":

    cmd = shlex.split("vault operator init")
    env = os.environ.copy()
    env["VAULT_ADDR"] = "https://127.0.0.1:8200"
    env["VAULT_SKIP_VERIFY"] = "true"
    res = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    stdout = res.stdout.decode().split("\n")
    unseal_keys = []
    print(res.stderr.decode())
    print("\n".join(stdout))
    for line in stdout:
        if "unseal key" in line.lower():
            unseal_keys.append(line.split(":")[-1].strip())
        if "initial root token" in line.lower():
            token = line.split(":")[-1].strip()
            break
    with open("/vault/keys", "w") as f:
        for nn, key in enumerate(unseal_keys):
            f.write(f"Unseal key #{nn+1}: {key}\n")
        f.write(f"Root token: {token}")

    for key in unseal_keys[:3]:
        run(shlex.split(f"vault operator unseal {key}"), env=env)
    run(shlex.split(f"vault login {token}"), env=env)
    run(shlex.split(f"vault secrets enable -path=kv kv"), env=env)
    run(shlex.split(f"vault policy write read-eval /vault/policy-file.hcl"), env=env)
    run(shlex.split(f"vault auth enable cert"), env=env)
    run(
        shlex.split(
            "vault write auth/cert/certs/app policies=web,prod,file,read-eval certificate=@/mnt/freva.crt"
        ),
        env=env,
    )
