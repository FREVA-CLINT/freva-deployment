#!/usr/bin/env python3

import argparse
from pathlib import Path


def parse_args(argv=None):

    app = argparse.ArgumentParser(
        "apache_config_parsers", description="Create the right apache configuration."
    )
    app.add_argument("input_file", type=Path, help="Input configuration")
    app.add_argument(
        "output_file",
        type=Path,
        help="Target configfile",
        default=Path("/etc/apache2/sites-available"),
    )
    app.add_argument(
        "--website", type=str, default="www.freva.org", help="Set the website"
    )
    app.add_argument("--root-dir", type=Path, help="Set the project root path"),
    app.add_argument("--work-dir", type=Path, help="Set the project root path"),
    app.add_argument("--project-name", type=str, help="Set the name of the project")
    app.add_argument("--alias", type=str, help="Set the server alias")
    app.add_argument("--python", type=str, help="Set the python version")
    app.add_argument("--server-name", type=str, help="Set the name of the host system")
    args = app.parse_args()
    return args


def edit_config(
    args,
    project_root="/srv/http",
    variables=(
        "website",
        "root_dir",
        "work_dir",
        "project_name",
        "server_name",
        "python_vers",
    ),
):
    """Edit the configuration file."""
    with args.input_file.open() as f:
        inp_config = f.read().replace("%PROJECT_ROOT", project_root)
    alias = args.alias
    kwargs = dict(args._get_kwargs())
    kwargs["website"] = "https://" + kwargs["website"].replace("http://", "").replace(
        "https://", ""
    )
    kwargs["python_vers"] = f'python{kwargs["python"]}'
    if alias and alias != "none":
        alias = f'\n{8*" "}'.join(
            [f"ServerAlias {a.strip()}" for a in alias.split(",") if a.strip()]
        )
        inp_config = inp_config.replace("#ServerAlias %SERVER_ALIAS", alias)
    for v in variables:
        inp_config = inp_config.replace(f"%{v.upper()}", str(kwargs[v]))
    with args.output_file.open("w") as f:
        f.write(inp_config)


if __name__ == "__main__":

    import sys

    edit_config(parse_args())
