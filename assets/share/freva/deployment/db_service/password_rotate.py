#!/usr/bin/env python3

import os
import random
import shlex
from subprocess import run
import string

import requests

SQL_ENTRY = (
    "mysql -h {host} -u root -p'{root_pw}' -e "
    "\"FLUSH PRIVILEGES; ALTER USER {user}@'%' IDENTIFIED BY "
    "'{passwd}'; FLUSH PRIVILEGES\""
)


def gen_passwd(
    num_chars: int = 20, num_digits: int = 4, num_punctuations: int = 4
) -> str:
    """Generate a new mysql db user password."""

    num_chars -= num_digits + num_punctuations
    punctuations = "!@$^&*()_+-;:|,.%"
    possible_characters = [
        "".join(random.sample(string.ascii_letters, num_chars)),
        "".join(random.sample(string.digits, num_digits)),
        "".join(random.sample(punctuations, num_punctuations)),
    ]
    characters = "".join(possible_characters)
    return "".join(random.sample(characters, len(characters)))


def set_passwd_in_sql_server(passwd: str) -> None:
    """Set the new password of the sql user."""

    root_pw = os.environ["MYSQL_ROOT_PASSWORD"]
    url = f'http://{os.environ["HOST"]}:5002/vault/{passwd}/{root_pw}'
    cmd = SQL_ENTRY.format(
        user=os.environ["DB_USER"],
        passwd=passwd,
        host="localhost",
        root_pw=root_pw,
    )
    _ = run(shlex.split(cmd), check=True)
    requests.post(url).json()


if __name__ == "__main__":
    set_passwd_in_sql_server(gen_passwd())
