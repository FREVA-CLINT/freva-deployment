# Transitioning of the Plugins

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


## Transitioning steps:

There are multiple ways of how you can get your old plugin back to the new
Freva system. We do recommend a deployment strategy involving conda.
While this strategy is not strictly necessary it offers the best as
possible reproducibility and is host system independent.
Meaning your plugins can be easily transitioned to other institutions and
are more likely to work after major system updates on your host system.
Here we briefly cover the steps that are needed to bring your old plugin back
to life in the new Freva system. We will also discuss alternatives
to using conda. Regardless of choice on using conda or not the first two
steps will be necessary.

### Common steps:

1. clone the repository of a plugin, change into the directory and create a new branch.

2. export the user plugin variable:
```console
export EVALUATION_SYSTEM_PLUGINS=$PWD/path_to_wrapper_file,class_name
freva plugin -l
```
Most certainly, the plugin manager will output a warning that the plugin could
not be loaded. If it does, change the plugin accordingly to make the
warning messages go away.

### a. Using conda:
As mentioned above this step has the advantage that you increase the reproducibility
of your plugin. Transitioning your plugin to other institutions is also easy
because all libraries are encapsulated from the host system and hence independent.
While not strictly necessary it is a good idea to familiarise yourself with
[anaconda](https://docs.conda.io/projects/conda/en/latest/user-guide/index.html).

3. Download the [conda environment file template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/plugin-env.yml) and the [Makefile template](https://swift.dkrz.de/v1/dkrz_3d3c7abc-1681-4012-b656-3cc1058c52a9/k204230/freva-transition/Makefile)

4. Add all dependencies to the `plugin-env.yml` file. In doubt search [anaconda.org](https://anaconda.org) for dependencies.

5. If needed adjust the `build` step in the `Makefile` for compiling plugin dependencies, e.g. fortran dependencies.

6. Execute `make all` to install the conda environment and build the plugin dependencies.

7. Execute the plugin and check if everything goes well.

8. Format the plugin using black: `black -t py310 path_to_plugin.py`

### b. Using the environment of freva
If your plugin doesn't need many libraries you can simply try to use everything
the comes with freva. This is the easiest way as you don't have to do anything.
Simply try to execute all commands that come with your plugin and see what
happens.

### c. Using software of the host system
You can also make use of the software installed on the host system. For
example via spack. Many HPC systems offer the `module` command. Using this
approach will result in a plugin that is tailored around the current host system
you are using. Future updates may break usage and you defiantly won't be able
to use your plugin at other institutions.

## Transitioning `python2` plugins
Python plugins (especially python2) need special care. The recommended strategy
is to convert the plugin content to python3. If this is not possible an anaconda
python2 environment should be created.

If in the original plugin the plugin code is directly executed in the `run_rool`
method (formerly named `runTool`) this code has to be split from the new `run_tool` method. The
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

def run_tool(self, config_dict={}):
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
    return self.prepare_output(config_dict["output_dir"])
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

If you want to use the json file in a bash script you must install the `jq`
json parser. Simply add `jq` to your `plugin-env.yml` file and read the
[docs of jq](https://stedolan.github.io/jq/tutorial/).

## After conda deployment: Increasing reproducibility of your plugin
If you have successfully deployed your plugin environment using conda you
can increase the reproducibility by "freezing" all packages that have
been installed by conda. This will increase the reproducibility of your package
because the versions of your packages will exactly match the one you are
using at this point in time. Every time you re-install the plugin environment
you will have the same dependency versions. To fix the package versions
execute the following command:
```
./plugin_env/bin/conda list  --explicit > spec-file.txt
```
Add and commit the created `spec-file.txt` to your repository. Afterwards
you can replace
`conda env create --prefix ./plugin_env -f plugin-env.yml --force` in the `conda`
section of your `Makefile` by:

```
conda env create --prefix ./plugin_env -f spec-file.txt --force
```
And you're done.

## Problem: conda doesn't finish resolving dependencies
Sometimes conda is unable/won't finish to solve all dependencies. You have a
couple of options in that case. First you can try replacing the `conda` command
by `mamba` in your Makefile. `mamba` is written in C and comes with a
different dependency solver. Most of the time switching from `conda` to `mamba`
solves the problem. If the issues persists with `mamba` you can try identifying
the problematic package(s). Usually by guessing which package(s) might be the
offending ones and removing them from the `plugin-env.yml` file. Once the
package(s) have been circled you can create an additional conda environment.
For example by adding the following line into the `conda` section of the
`Makefile`. For example:

```
conda create -c conda-forge -p ./plugin_env2 cdo netcdf-fortran
``

If you want to use resources from this environment in your plugin you need
to modify the environment in your API wrapper. Following the example
above, this modification could look like this:

```python
env = os.environ.copy()
this_dir = os.path.dirname(os.path.abspath(__file__))
env["PATH"] = env["PATH"] + ":" + os.path.join(this_dir, "plugin_env2", "bin")
env["LD_LIBRARY_PATH"] = os.path.join(this_dir, "plugin_env2", "lib")
self.call(your_command_here, env=env)

```
If you need to compile additional libraries you probably also want to adjust
the `PATH` and `LD_LIBRARY_PATH` variable in the file that executes the compile
step to be able to pick up the `lib` and `bin` folders in the `plugin_env2`
conda environment.
