# Transitioning guide

The following serves as a guide to transition an existing freva instance
(within the python*2* frame work) to the new (python*3* based) version.

We have created a small command line interface (`freva-migrate`) that
helps migrating content of an existing freva framework to the new one.
The `freva-migrate` command has two sub commands:

```bash
freva-migrate --help
usage: freva-migrate [-h] [-v] {database,drs-config} ...

Utilities to handle migrations from old freva systems.

positional arguments:
  {database,drs-config}
                        Migration commands:
    database            Use this command to migrate an existing freva database to a recently set up
                        system.
    drs-config          Migrate old drs structure definitions to new toml style.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Verbosity level (default: 0)

```

## Transition to new DRS Config

In the old version the DRS File configuration, that is the definitions
defining the metadata of datasets, was hard coded into the module
`evaluation_system.model.file`. In the new version this configuration
is saved in a designated [toml](https://toml.io/en/) file (drs_confif.toml).
To read an existing DRS Configuration from an 'old' instance of freva and
convert it to the new freva DRS Config toml file use the `drs-config` sub-coammand
of the `freva-migrate` command line interface.

```
freva-migrate drs-config --help
usage: freva-migrate drs-config [-h] [--python-path python-path]

Freva drs structure migration

options:
  -h, --help            show this help message and exit
  --python-path python-path
                        Python path of the old freva instance, leave blank if you loaded the old freva
                        module / source file. (default: None)
```

> **_Note:_** You can either load/source the old freva instance or simply point the `--python-path` option to the python path of the old freva.

Once the command has been executed the resulting `drs_config.toml` should be
place next to the `evaluation_system.conf` file. That is the `freva` folder within the
`root_dir` location of the new freva instance, for example `/mnt/project/freva`.



## Transition to new Database
The new system has witnessed small changes to the database structure the `database`
sub-command of the `freva-migrate` command helps to transition to this new
database structure. To migrate a database of a old installation of the freva
system to a freshly deployed freva instance used the following command:

```
freva-migrate database --help
usage: freva-migrate database [-h] [--python-path PYTHON_PATH] [--domain DOMAIN] project-name cert-file

Freva database migration

positional arguments:
  project-name          The project name for the recently deployed freva system
  cert-file             Path to the public certificate file.

options:
  -h, --help            show this help message and exit
  --python-path PYTHON_PATH
                        Python path of the old freva instance, leave blank if you load the old freva
                        module / source file. (default: None)
  --domain DOMAIN       Domain name of your organisation to create a uniq identifier. (default: dkrz)
```

The `cert-file` positional argument refers the public certificate file that was
created during the deployment process and is needed to establish a connection to
the new database. You can either use the one that has been
saved by the deployment or use it from the freva config directory. By default
the certificate file resides within `freva` path of the deployment `root_dir`
for example `/mnt/project/freva/project.crt`. Also don't forget to set the domain
name for your institution as a unique identifier.

After the command has been applied the new database with its "old" content from
the previous freva instance will be ready for use.

## Transitioning of the Plugins

The freva plugins are an essential part of freva.
Most likely the transitioning from the old python2 to the new python3 based
system, needs special care. A complete rewrite of the plugin manager is planned.
This section should therefore seen as intermediate solutions for plugin transitioning.

Currently we recommend creating an anaconda environment for each plugin.
This approach has several advantages:

- reproducible as each plugin will get a anaconda environment file
- no version and dependency conflicts occur.
- once set up easy to maintain.

These are the disadvantages of this method:

- A anaconda environment file has to be created for each plugin.


### Transitioning steps:

1. clone the repository of a plugin, change into the directory and create a new branch.

2. export the user plugin variable:

```bash

export EVALUATION_SYSTEM_PLUGINS=$PWD/path_to_wrapper_file,class_name

freva plugin -l

```

Most certainly the plugin manger will output a warning, that the plugin could not be loaded.
If it does change the plugins accordingly to make the warning messages go away.

3. Download the [conda environment file template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/plugin-env.yml) and the [Makefile template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/Makefile)

4. Add all dependencies to the `plugin-environment.yml` file. In doubt search [anaconda.org](https://anaconda.org) for dependencies.

5. If needed adjust the `build` step in the `Makefile` for compiling plugin dependencies, e.g. fortran dependencies.

6. Execute `make all` to install the conda environment and build the plugin dependencies.

7. Execute the plugin and check if everything goes will.

8. Format the plugin using black: `black -t py310 path_to_plugin.py`

### Transitioning `python2` plugins
Python plugins (especially python2) need special care. The recommended strategy
is to convert the plugin content to python3. If this is not possible an anaconda
python2 environment should be created.

If in the original plugin the plugin code directly executed in the `runTool`
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
