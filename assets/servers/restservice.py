#!/usr/bin/env python3
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import os
from typing import NamedTuple

from flask import Flask, request
from flask_restful import reqparse, Resource, Api
import toml

ServiceInfo = NamedTuple(
    "ServiceInfo", [("name", str), ("python_path", str), ("hosts", str)]
)


class ServerBaseClass:
    """Base class for looking/saving server information from/to disk."""

    def __init__(self):
        self.server_information: dict[str, list[ServiceInfo]] = defaultdict(
            list[ServiceInfo]
        )
        self.server_info_file.touch()
        self.update_server_information()

    @property
    def server_info_file(self) -> Path:
        """Path to the filename holding the server infromation."""
        return Path(os.environ["SERVER_FILE"])

    def update_server_information(self) -> None:
        """Read the server information."""
        with self.server_info_file.open() as f_obj:
            server_dict = toml.load(f_obj)
        for project, settings in server_dict.items():
            for service, (python_path, hosts) in settings.items():
                self.server_information[project].append(
                    ServiceInfo(name=service, python_path=python_path, hosts=hosts)
                )

    def _update(self) -> None:
        with self.server_info_file.open("w") as f_obj:
            toml.dump(self._server_info_tuple_to_dict(), f_obj)
        self.update_server_information()

    def _server_info_tuple_to_dict(self) -> dict[str, dict[str, tuple[str, str]]]:
        """Convert ServiceInfo namedtuple to dictionary."""
        dump_dict: dict[str, dict[str, tuple[str, str]]] = {}
        for project, settings in self.server_information.items():
            dump_dict[project] = {}
            for settings_tuple in settings:
                dump_dict[project][settings_tuple.name] = (
                    settings_tuple.python_path,
                    settings_tuple.hosts,
                )
        return dump_dict


class ServerLookup(ServerBaseClass, Resource):
    """Lookup server information."""

    def __init__(self):
        super().__init__()

    def get(self) -> tuple[dict[str, dict[str, tuple[str, str]]], int]:
        """Get method, for getting server information.

        Returns:
        --------
            dict[str dict[str, tuple[str, str]]]:  sever information
        """
        dump_dict = self._server_info_tuple_to_dict()
        return dump_dict, 200


class ServerEntry(ServerBaseClass, Resource):
    """Add entries to the server map."""

    def __init__(self):
        super().__init__()

    def put(self, project: str) -> tuple[str, int]:
        """Put method, for setting a server entry.

        Parameters
        -----------
        project: str
            The freva project name which is updated.

        Returns
        --------
            dict: status information
        """
        try:
            config = toml.loads(request.form["config"])
        except toml.TomlDecodeError as error:
            return error.__str__(), 400
        for service, settings in config.items():
            try:
                settings_tuple = ServiceInfo(name=service, **settings)
            except TypeError:
                return "TypeError: Wrong settings", 400
            self.server_information[project].append(settings_tuple)
        try:
            self._update()
        except Exception as e:
            return e.__str__(), 500
        return "updated", 201

    def get(self, project: str) -> tuple[dict[str, tuple[str, str]], int]:
        """Get method, for getting server information.

        Parameters
        -----------
        project: str
            The freva project name which is queried.

        Returns:
        --------
            dict[str, tuple[str, str]]:  sever information
        """

        try:
            return (
                self._server_info_tuple_to_dict()[project],
                200,
            )
        except KeyError:
            return f"No such project: {project}", 404


class ServerStaus(Resource):
    """Get and set the staus of services."""

    service_status: dict[str, dict[str, dict[str, str]]] = {}

    def get(self, project: str, service: str) -> tuple[dict[str, str], int]:
        """Get method for retreivng the service status.

        Parameters
        ----------
        project: str
            The freva project name which is updated.
        service: str
            Name of the service which status is retreived
        """
        try:
            return self.service_status[project][service], 200
        except KeyError:
            return f"No such service: {service}", 404

    def put(self, project: str, service: str) -> tuple[str, int]:
        """Put method, for setting the service status.

        Parameters
        -----------
        project: str
            The freva project name which is updated.

        Returns
        --------
            dict: operation status information
        """
        keys = ("mem", "status", "cpu")
        args = {k: v.lower() for (k, v) in request.form.items() if k in keys and v}
        if project not in self.service_status:
            self.service_status[project] = {service: args}
        else:
            for key, value in args.items():
                try:
                    self.service_status[project][service][key] = value
                except KeyError:
                    self.service_status[project][service] = {key: value}
        return "updated", 201


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(ServerLookup, "/")
    api.add_resource(ServerEntry, "/<string:project>")
    api.add_resource(ServerStaus, "/<string:project>/<string:service>")
    app.run(host="0.0.0.0", port=5008)
