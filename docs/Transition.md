

# Transitioning guide

The following serves as a guide to transition an existing freva instance (within the python*2* frame work) to the new (python*3* based) version.

## Transition to new DRS Config

In the old version the DRS File configuration, that is the definitions defining the metadata of datasets, was hard coded into the module `evaluation_system.model.file`. In the new version this configuration is saved in a designated [toml](https://toml.io/en/) file (drs_confif.toml). To read an existing DRS Configuration from an 'old' instance of freva and convert it to the new freva DRS Config toml file use the following script:


I will create a script soon.


Once the script has been created place the resulting `drs_config.toml` next to the `evaluation_system.conf` file into the `freva` folder within the `root_dir` location of the new freva instace, for example `/mnt/poroject/freva`.


## Transitioning of the Plugins

The freva plugins are an essential part of freva. Most likely the the transitioning from the old python2 to the new python3 based system, needs special care. A complete rewrite of the plugin manager is planned. This section should therefore seen as intermediate solutions for plugin transitioning. Generally there are three possibilities to transition the plugins. All of which come with advantages and disadvantages which should be outlined and discussed below. Please read the transitioning steps for each proposed transitioning guides and pick a method depending on your preferences:


**Note:** Currently there is a development version installed on mistral which can be made available by executing the following command:

```bash
module load clint regiklim-ces/2022.03
```


### I Plugin transitioning using the module system

This method makes use of an available modules system. Hence modules has to be set up on the system.

Below are the advantages of this method

- Third party software such as R and additional libraries are dealt with by the modules system.

Below you find drawbacks of this method:

- modules on the system change over time. Hence reproducibility is not guaranteed neither is functionality if dependencies are updated by the system admins

- software that is not available via modules system needs to be installed by hand (which is especially true for levante)

- module names change from system to system. Hence plugins have to be adopted to run on each HPC system. Over the long run the plugin code might diverge.

Overall I think this method is the leas favourable of all outlined methods. We should not use this method.

All steps assume that a new version of the core library is installed and configured.

#### Transitioning steps:

1. clone the repository of a plugin, change into the directory and create a new branch.

2. export the user plugin variable:

```bash

export EVALUATION_SYSTEM_PLUGINS=$PWD/path_to_wrapper_file,class_name

freva plugin -l

```

Most certainly the plugin manger will output a warning, that the plugin could not be loaded. If it does change the plugins accordingly to make the warning messages go away.

3. Once the plugin manager can load the plugins and the `freva plugin -l` command shows the plugin you have to load the right modules in the plugin if needed.

4. If needed build plugin dependencies, e.g fortran source code.

4. Execute the plugin and check if everything goes will.

5. Fromat the plugin using black


### II Plugin transitioning using a common plugin anaconda environment

This method uses a common anaconda environment for all plugins. The plugin anaconda environment can be made available via the modules system. Below are the advantages of this method:

- Once all dependencies are installed into the common anaconda environment, no special care has to be taken about the plugin transitioning.

This are the disadvantages of this method:

- Version mismatches and dependency conflicts might occur.
- Not really reproducible, if noone keeps track of installed packages.


#### Transitioning steps:

1. clone the repository of a plugin, change into the directory and create a new branch.

2. export the user plugin variable:

```bash

export EVALUATION_SYSTEM_PLUGINS=$PWD/path_to_wrapper_file,class_name

freva plugin -l

```

Most certainly the plugin manger will output a warning, that the plugin could not be loaded. If it does change the plugins accordingly to make the warning messages go away.

3. If needed build plugin dependencies, e.g fortran source code.
4. Execute the plugin and check if everything goes will.
5. Fromat the plugin using black


### III Creating a designated anaconda environment for each plugin.

In this method each plugin gets its own anaconda environment.

Below are the advantages of this method:

- reproducible as each plugin will get a anaconda environment file
- no version and dependency conflicts occur.
- once set up easy to maintain.

These are the disadvantages of this method:

- A anaconda environment file has to be created for each plugin.
- The plugin manager has to be update to patch the PATH environment variable.


#### Transitioning steps:

1. clone the repository of a plugin, change into the directory and create a new branch.

2. export the user plugin variable:

```bash

export EVALUATION_SYSTEM_PLUGINS=$PWD/path_to_wrapper_file,class_name

freva plugin -l

```

Most certainly the plugin manger will output a warning, that the plugin could not be loaded. If it does change the plugins accordingly to make the warning messages go away.

3. Download the [conda environment file template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/plugin-env.yml) and the [Makefile template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/Makefile)

4. Add all dependencies to the `plugin-environment.yml` file. In doubt search [anaconda.org](https://anaconda.org) for dependencies.

5. If needed adjust the `build` step in the `Makefile` for compiling plugin dependencies, e.g. fortran dependencies.

6. Execute `make all` to install the conda environment and build the plugin dependencies.

7. Execute the plugin and check if everything goes will.

8. Fromat the plugin using black

### Transitioning `python2` plugins
Python plugins (especially python2) need special care. The recommended strategy
is to convert the plugin content to python3 if this is not possible a anaconda
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

