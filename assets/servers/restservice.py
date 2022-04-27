#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import os
from typing import NamedTuple

from flask import Flask, request
from flask_restful import reqparse, Resource, Api
import toml

ServiceInfo = NamedTuple(
    "ServiceInfo", [("name", str), ("python_path", str), ("hosts", str)]
)


class ServerLookup(Resource):
    """Lookup server information."""

    def __init__(self):
        self.server_information: dict[str, list[ServiceInfo]] = {}
        self.update_server_information()

    def update_server_information(self) -> None:
        """Read the server information."""
        try:
            with Path(os.environ["SERVER_FILE"]).open() as f_obj:
                server_dict = toml.load(f_obj)
        except FileNotFoundError:
            return
        for project, settings in server_dict.items():
            for service, (python_path, hosts) in settings.items():
                try:
                    self.server_information[project].append(
                        ServiceInfo(name=service, python_path=python_path, hosts=hosts)
                    )
                except KeyError:
                    self.server_information[project] = [
                        ServiceInfo(name=service, python_path=python_path, hosts=hosts)
                    ]

    def _update(self) -> tuple[int, str]:
        try:
            with Path(os.environ["SERVER_FILE"]).open("w") as f_obj:
                toml.dump(self._server_info_tuple_to_dict(), f_obj)
            self.update_server_information()
        except Exception as error:
            return 500, error.__str__()
        return 201, "updated"

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

    def get(self):
        """Get method, for getting server information.

        Returns:
        --------
            dict[str dict[str, tuple[str, str]]]:  sever information
        """
        dump_dict = self._server_info_tuple_to_dict()
        return dump_dict, 200


class ServerEntry(ServerLookup):
    """Add entries to the server map."""

    def __init__(self):
        super().__init__()

    def put(self, project):
        """Post method, for setting a server entry.

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
            return 500, dict(status=error.__str__())
        for service, settings in config.items():
            try:
                settings_tuple = ServiceInfo(name=service, **settings)
            except TypeError:
                return 500, dict(message="TypeError: Wrong settings")
            try:
                self.server_information[project].append(settings_tuple)
            except KeyError:
                self.server_information[project] = [settings_tuple]
        code, msg = self._update()
        return {}, code, {"message": msg}

    def get(self, project):
        """Get method, for getting server information.

        Parameters
        -----------
        project: str
            The freva project name which is queried.

        Returns:
        --------
            dict[str, tuple[str, str]]:  sever information
        """

        dump_dict = self._server_info_tuple_to_dict()
        try:
            return self._server_info_tuple_to_dict()[project], 200
        except KeyError:
            return {}, 404, {"message": f"No such project: {project}"}


service_status: dict[str, dict[str, dict[str, str]]] = {}


class ServerStaus(Resource):
    """Get and set the staus of services."""

    def get(self, project, service):
        """Get method for retreivng the service status.

        Parameters
        ----------
        project: str
            The freva project name which is updated.
        service: str
            Name of the service which status is retreived
        """
        try:
            return service_status[project][service], 200
        except KeyError:
            return {}, 404, {"message": "No such project/service"}

    def put(self, project: str, service: str):
        """Post method, for setting the service status.

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
        if not service_status:
            service_status[project] = {service: args}
        elif project not in service_status:
            service_status[project] = {service: args}
        else:
            for key, value in args.items():
                try:
                    service_status[project][service][key] = value
                except KeyError:
                    service_status[project][service] = {key: value}
        return {}, 201


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(ServerLookup, "/")
    api.add_resource(ServerEntry, "/<string:project>")
    api.add_resource(ServerStaus, "/<string:project>/<string:service>")
    app.run(host="0.0.0.0", port="5008")
