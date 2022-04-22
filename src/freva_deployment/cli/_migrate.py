"""CLI to assist with migrating the system."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import os
import shlex
import shutil
from subprocess import run, PIPE, CalledProcessError
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import cast, TextIO

import pymysql
import toml

from ..utils import (
    logger,
    read_db_credentials,
    download_server_map,
    get_setup_for_service,
    set_log_level,
    guess_map_server,
)

DUMP_SCRIPT = """#!{python_bin}
import json
import sys
sys.path.insert(0, "{python_path}")
from evaluation_system.model.file import DRSFile

with open("{json_file}", "w") as f_obj:
    json.dump(DRSFile.DRS_STRUCTURE, f_obj)
"""

DB_SCRIPT = """#!{python_bin}
import json
import sys
sys.path.insert(0, "{python_path}")
from evaluation_system.misc import config
config.reloadConfiguration()
dump_cfg = {{"db.port": config.get("db.port", 3306)}}
for key in ("db.db", "db.passwd", "db.user", "db.host"):
    dump_cfg[key] = config.get(key)
with open("{json_file}", "w") as f_obj:
    json.dump(dump_cfg, f_obj)
"""


def exec_command(
    command: str, stdout: TextIO | None = None, shell: bool = False
) -> None:
    """Execute a sub process command."""
    logger.debug("Executing command: %s", command)
    env = os.environ.copy()
    _ = env.pop("EVALUATION_SYSTEM_CONFIG_FILE", "")
    std = stdout or PIPE
    res = run(
        shlex.split(command), stdout=std, stderr=PIPE, shell=shell, env=env, check=False
    )
    try:
        res.check_returncode()
    except CalledProcessError as error:
        logger.error("Script returned non-zero exit status:\n%s", command)
        logger.error("STDERROR:\n%s", res.stderr.decode())
        raise error


def execute_script_and_get_config(python_bin: Path, template: str) -> str:
    """Execute a python2 template and read it's ouput."""
    logger.debug("Working on %s", python_bin)
    python_path = python_bin.parents[3] / "freva" / "src"
    with TemporaryDirectory() as temp_dir:
        logger.debug("Creating temporary script in %s", temp_dir)
        with open(Path(temp_dir) / "write.py", "w") as f_obj:
            script = template.format(
                python_bin=python_bin,
                python_path=python_path,
                json_file=Path(temp_dir) / "config.json",
            )
            logger.debug("Writing script:\n%s", script)
            f_obj.write(script)
        exec_command(f"{python_bin} {Path(temp_dir) / 'write.py'}")
        logger.debug("Reading json file:")
        with open(Path(temp_dir) / "config.json") as f_obj:
            return f_obj.read()


def _get_python_path_from_env() -> Path:
    python_path = cast(str, shutil.which("python"))
    return Path(python_path)


def _add_new_db(db_config: dict[str, str], dump_file: str) -> None:
    dump_cmd = (
        f"mysql -h {db_config['db.host']} -u {db_config['db.user']} "
        f"-p'{db_config['db.passwd']}' -P{db_config['db.port']} < {dump_file}"
    )
    logger.debug("Executing command: %s", dump_cmd)
    res = os.system(dump_cmd)
    if res != 0:
        logger.error("Command failed: %s", dump_cmd)
        return
    with pymysql.connect(
        autocommit=True,
        host=db_config["db.host"],
        user=db_config["db.user"],
        password=db_config["db.passwd"],
        port=int(db_config["db.port"]),
    ) as con:
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_SCHEMA='{db_config['db.db']}' AND "
                "TABLE_NAME='history_history' AND column_name='host'"
            )
            results_found = cursor.fetchall()[0][0]
            if results_found == 0:
                logger.info("Adding new column `host` to table..")
                cursor.execute("ALTER TABLE history_history ADD host longtext")


def _migrate_db(parser: argparse.Namespace) -> None:
    server_map = guess_map_server(parser.server_map)
    python_path = parser.python_path or _get_python_path_from_env()
    mysqldump = shutil.which("mysqldump")
    if mysqldump is None:
        logger.error("myslqdump not found, to continue isntall mysqldump")
        return
    config = json.loads(execute_script_and_get_config(python_path, DB_SCRIPT))
    try:
        deploy_config = download_server_map(server_map)[parser.project_name]
    except KeyError as error:
        logger.error("Config Error for project %s", parser.project_name)
        raise error
    try:
        _, db_host = get_setup_for_service("db", deploy_config)
    except (KeyError, AttributeError) as error:
        raise KeyError("Could not find db host in config") from error
    new_db_cfg = read_db_credentials(parser.cert_file, db_host)
    with NamedTemporaryFile(suffix=".sql") as temp_file:
        with open(temp_file.name, "w") as f_obj:
            f_obj.write(f"USE `{new_db_cfg['db.db']}`;\n")
            f_obj.flush()
            dump_command = (
                f"{mysqldump} -u {config['db.user']} "
                f"-h {config['db.host']} -p'{config['db.passwd']}' "
                f"-P{config['db.port']} "
                "--tz-utc --no-create-db "
                f"{config['db.db']}"
            )
            exec_command(dump_command, stdout=f_obj)
            _add_new_db(new_db_cfg, temp_file.name)


def _migrate_drs(parser: argparse.Namespace) -> None:
    python_path = parser.python_path or _get_python_path_from_env()
    config = json.loads(execute_script_and_get_config(python_path, DUMP_SCRIPT))
    logger.debug("Writing toml file to drs_config.toml")
    this_file = (Path(".") / "drs_config.toml").absolute()
    with open(this_file, "w") as f_obj:
        toml.dump(config, f_obj)
    logger.info(
        "Toml file has been written to %s, you can copy the file to its new "
        "location next to the evaluation_system.conf file\n Note: The "
        "evaluation_system.conf location is set by the "
        "EVALUATION_SYSTEM_CONFIG_FILE environment variable after the new "
        "module has been loaded | is sourced.",
        this_file,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Construct command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="freva-migrate",
        description="Utilities to handle migrations from old freva systems.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    subparsers = parser.add_subparsers(help="Migration commands:", required=True)
    db_parser = subparsers.add_parser(
        "database",
        description="Freva database migration",
        help="Use this command to migrate an existing freva database "
        "to a recently set up system.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    db_parser.add_argument(
        "project_name",
        metavar="project-name",
        type=str,
        help="The project name for the recently deployed freva system",
    )
    db_parser.add_argument(
        "cert_file",
        metavar="cert-file",
        type=Path,
        help="Path to the public certificate file.",
    )
    db_parser.add_argument(
        "--python-path",
        type=Path,
        default=None,
        help="Python path of the old freva instance, leave blank "
        "if you load the old freva module / source file.",
    )
    db_parser.add_argument(
        "--server-map",
        type=str,
        default=None,
        help=(
            "Hostname of the service mapping the freva server "
            "archtiecture, Note: you can create a server map by "
            "running the deploy-freva-map command"
        ),
    )
    db_parser.set_defaults(apply_func=_migrate_db)
    drs_parser = subparsers.add_parser(
        "drs-config",
        description="Freva drs structure migration",
        help="Migrate old drs structure definitions to new toml style.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    drs_parser.add_argument(
        "--python-path",
        metavar="python-path",
        type=Path,
        help="Python path of the old freva instance, leave blank "
        "if you load the old freva module / source file.",
    )
    drs_parser.set_defaults(apply_func=_migrate_drs)
    arg = parser.parse_args(argv)
    return arg


def cli() -> None:
    """Run the command line interface."""
    arg = parse_args(sys.argv[1:])
    set_log_level(arg.verbose)
    arg.apply_func(arg)
