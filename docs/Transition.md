# Appendix II: Transitioning guide

The following serves as a guide to transition an existing Freva instance
(within the python*2* frame work) to the new (python*3* based) version.


## Transition to new Database
We have created a small command line interface (`freva-migrate`) that
helps migrating content of an existing Freva framework to the new one.
The `freva-migrate` command has currently one sub commands:

The new system has witnessed small changes to the database structure. The `database`
sub-command of the `freva-migrate` command helps to transition to this new
database structure. To migrate a database of an old installation of the Freva
system to a freshly deployed Freva instance use the following command:

```
usage: freva-migrate database [-h] [--old-port OLD_PORT] [--old-db OLD_DB] [--old-pw OLD_PW] [--old-user OLD_USER]
                              new_hostname old_hostname cert-file

Freva database migration

positional arguments:
  new_hostname         The hostname where the new database is deployed.
  old_hostname         Hostname of the old database.
  cert-file            Path to the public certificate file.

options:
  -h, --help           show this help message and exit
  --old-port OLD_PORT  The port where the old database server is running on. (default: 3306)
  --old-db OLD_DB      The name of the old database (default: evaluationsystem)
  --old-pw OLD_PW      The passowrd to the old database (default: None)
  --old-user OLD_USER  The old database user (default: evaluationsystem)
```

The `cert-file` positional argument refers to the public certificate file that was
created during the deployment process and is needed to establish a connection to
the new database (via the vault). You can either use the one that has been
saved by the deployment or use it from the freva config directory. By default
the certificate file resides within `freva` path of the deployment `root_dir`
for example `/mnt/project/freva/project.crt`. Also don't forget to set the domain
name for your institution as a unique identifier.

After the command has been applied the new database with its "old" content from
the previous Freva instance will be ready for use.


## Transition to new DRS Config

In the old version the DRS (Date Reference Syntax) File configuration, 
that is the definitions of dataset metadata, was hard coded into the module
`evaluation_system.model.file`. In the new version this configuration
is saved in a designated [toml](https://toml.io/en/) file (drs_config.toml).
The ingestion of data is done by the new `freva-ingest` software, which is
written in rust. More information on this configuration and usage of the
ingestion software can be found on the
[README](https://gitlab.dkrz.de/freva/freva-ingest).



## Transitioning of the Plugins

The Freva plugins are an essential part of Freva.
Most likely the transitioning from the old python2 to the new python3 based
system, needs special care. A complete rewrite of the plugin manager is planned.
This section should therefore be seen as intermediate solutions for plugin transitioning.

Currently we recommend creating an anaconda environment for each plugin.
This approach has several advantages:

- reproducible as each plugin will get a anaconda environment file.
- no version and dependency conflicts occur.
- once set up easy to maintain.

These are the disadvantages of this method:

- an anaconda environment file has to be created for each plugin.


### Transitioning steps:

1. clone the repository of a plugin, change into the directory and create a new branch.

2. export the user plugin variable:

```bash

export EVALUATION_SYSTEM_PLUGINS=$PWD/path_to_wrapper_file,class_name

freva plugin -l

```

Most certainly, the plugin manager will output a warning that the plugin could not be loaded.
If it does, change the plugins accordingly to make the warning messages go away.

3. Download the [conda environment file template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/plugin-env.yml) and the [Makefile template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/Makefile)

4. Add all dependencies to the `plugin-environment.yml` file. In doubt search [anaconda.org](https://anaconda.org) for dependencies.

5. If needed adjust the `build` step in the `Makefile` for compiling plugin dependencies, e.g. fortran dependencies.

6. Execute `make all` to install the conda environment and build the plugin dependencies.

7. Execute the plugin and check if everything goes well.

8. Format the plugin using black: `black -t py310 path_to_plugin.py`

### Transitioning `python2` plugins
Python plugins (especially python2) need special care. The recommended strategy
is to convert the plugin content to python3. If this is not possible an anaconda
python2 environment should be created.

If in the original plugin the plugin code is directly executed in the `runTool`
method this code has to be split from the `runTool` method. The
transition strategy is gathering the essential information in a `json` file that
is passed to the actual core part of the plugin. The code below shows a simple
python2 plugin:

```python

def runTool(self, config_dict={}):
    """This is the old `runTool` method.
    The plugin configuration is passed into this method and the code
    is directly executed in this method."""

    from src.plugin import calculate
    from evaluation_system.model.file import DRSFile
    search_kw = dict()
    search_kw["variable"] = config_dict["variable"]
    search_kw["model"] = config_dict["model"]
    search_kw["experiment"] = config_dict["experiment"]
    search_kw["ensemble"] = config_dict["ensemble"]
    search_kw["project"] = config_dict["project"]
    search_kw["product"] = config_dict["product"]
    search_kw["time_frequency"] = config["time_frequency"]
    files = files = sorted(DRSFile.solr_search(path_only=True, **search_kw))
    calculate(search_kw["variable"], files, config_dict["output_dir"])
    return self.prepareOutput(config_dict["output_dir"])
```

The above code should be split into two components, one that makes use of
`evaluation_system` to gather the data. And one that executes the actual plugin
code.

```python

def runTool(self, config_dict={}):
    """This is the wrapper API part of the plugin.
    It gathers the plugin information and passes the needed information
    to the actual plugin code that is split into another python file."""

    import json
    from evaluation_system.model.file import DRSFile
    from tempfile import NamedTemporaryFile
    from pathlib import Path
    search_kw = dict()
    search_kw["variable"] = config_dict["variable"]
    search_kw["model"] = config_dict["model"]
    search_kw["experiment"] = config_dict["experiment"]
    search_kw["ensemble"] = config_dict["ensemble"]
    search_kw["project"] = config_dict["project"]
    search_kw["product"] = config_dict["product"]
    search_kw["time_frequency"] = config["time_frequency"]
    files = sorted(DRSFile.solr_search(path_only=True, **search_kw))
    compute_kw = dict(variable=search_kw["variable"],
                      files=files,
                      output_dir=config_dict["output_dir"]
                )
    with NamedTemporaryFile(suffix=".json") as tf:
        with open(tf.name, "w"):
            json.dump(**compute_kw, f, indent=3)
        self.call(f"python2 {Path(__file__).parent / 'compute_python2'} {tf.name}")
    return self.prepareOutput(config_dict["output_dir"])
```

The below code demonstrates the usage of the above created `json` file.


```python
"""This file is the python2 plugin part.
This file calls the calculations of the python2 plugin. The configuration
is passed via a json file into this part.
"""

if __name__ == "__main__":
    from src.plugin import calculate
    import sys
    import json
    try:
        with open(sys.argv[1]) as f:
            config = json.load(f)
    except IndexError:
        raise ValueError("Usage: {} path_to_json_file.json".format(sys.argv[0]))
    calculate(config["variable"], config["files"], config["output_dir"])
```
