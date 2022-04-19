#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import os
from typing import Optional

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import toml


class ServerLookup(Resource):
    """Lookup server information."""

    _server_information: Optional[dict[str, dict[str, tuple[str, str]]]] = None

    @staticmethod
    def _read_server_information():
        try:
            with Path(os.environ["SERVER_FILE"]).open() as f_obj:
                return toml.load(f_obj)
        except FileNotFoundError:
            return {}

    def _update(self):
        with Path(os.environ["SERVER_FILE"]).open("w") as f_obj:
            toml.dump(self._server_information, f_obj)

    def put(self, project):
        """Post method, for setting a server entry.

        Parameters:
        -----------
        project: str
            Project name which servers settings are to be updated

        Returns:
        --------
            dict: status information
        """
        # Get the information from the vault
        config = toml.loads(request.form["config"])
        print(config)
        if self._server_information is None:
            self._server_information = self._read_server_information()
        for service, settings in config.items():
            try:
                self._server_information[project][service] = settings
            except KeyError:
                self._server_information[project] = {service: settings}
        print(self._server_information)
        self._update()
        return jsonify({"status": "success"})

    def get(self, project):
        """Get method, for getting server information.

        Parameters:
        -----------
        project: str
            Project name to query server information from.
        Returns:
        --------
            dict[str, tuple[str, str]]:  sever information
        """

        print(self._server_information)
        if self._server_information is None:
            self._server_information = self._read_server_information()
        return jsonify(self._server_information.get(project, {}))


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(ServerLookup, "/<project>")  # Route_3
    app.run(host="0.0.0.0", port=os.environ["PORT"])
