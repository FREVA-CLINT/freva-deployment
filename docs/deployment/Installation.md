# Installing freva-deployment
This section gives an overview over how to install the deployment software for
freva.

The main work will be done by [ansible](https://docs.ansible.com/ansible/latest/index.html),
hence some level of familiarity with ansible is advantageous but not necessary.
Since we are using ansible we can use this deployment routine from any workstation
computer (like a Mac-book). You do not need to run the deployment on the
machines where things get installed. The only requirement is
you can establish ssh connections to the servers via openSSH.

> ``💡`` In most cases openSSH clients should be available on your local machine.
> Windows users may refer to the
> [openSSH install page](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse?tabs=gui)
> for setting up openSSH on windows.

There are different ways to install the deployment software:

## 1. Using pre-built binaries.
You can download the pre-built binaries for your specific OS and architecture
from the [release page](release:{{version}}).

### Available Binaries

- **Linux**
  - [amd64](exe:linux-x64.tar.gz)
  - [arm64](exe:linux-arm64.tar.gz)
  - [armv7](exe:linux-armv7.tar.gz)
  - [ppc64le](exe:linux-ppc64le.tar.gz)
  - [s390x](exe:linux-s390x.tar.gz)
  - [i386](exe:linux-i386.tar.gz)

- **Windows**
  - [amd64](exe:windows-x64.zip)
  > ``💡`` This version uses a patched version of ansible. We can't guaranty
  > a working deployment software on windows.

- **macOS**
  - [amd64](exe:osx-x64.tar.gz)
  - [arm64](exe:osx-arm64.tar.gz)

After downloading version {{version}} file for your operating system and
architecture, you have to extract the archived folder (zip on windows,
tar.gz on Unix) and run the `deploy-freva` (`deploy-freva.exe` on windows)
command in the extracted folder:

```console
Usage: deploy-freva [-h] [-v] [-V] [--cowsay] {cmd,migrate} ...

Run the freva deployment

Positional Arguments:
  {cmd,migrate}
    cmd          Run deployment in batch mode.
    migrate      Utilities to handle migrations from old freva systems.

Options:
  -h, --help     show this help message and exit
  -v, --verbose  Verbosity level (default: 0)
  -V, --version  show program's version number and exit
  --cowsay       Let the cow speak! (default: False)
```


## 2. Installation via pip.
If you're using Linux, OsX or a Windows subsystem for Linux (WSL) you can
use *pip* to install the deployment software:

```console
python3 -m pip install -U freva-deployment
```

This command installs ansible and all required python packages.
> ``💡``  On *CentOS* python SELinux libraries need to be installed.
> You will need to install libselinux for your CentOS version.
>
> The ansible library is not supported on *Windows* and needs to be patched.
> you can either use the above mentioned pre compiled windows binary or install
> the deployment software on Windows Subsystem for Linux - WSL (preferred).

```console
python3 -m pip install libselinux-python3
```
## 3. Using docker

A pre-built docker image is available to run the deployment

```console
docker run -it -v /path/to/config:/opt/freva-deployment:z ghcr.io/freva-clint/freva-deployment
```
The `-it` flags are important in order to interact with the program. To use
and save existing configurations you can mount the directories of the config
files into the container.


## Sub Commands after installation:
The deployment software consists of *three* different sub-commands:
- `deploy-freva`: Main deployment command via text user interface (tui).
- `deploy-freva cmd`: Run already configured deployment.
- `deploy-freva migrate`: Command line interface to manage project migration from
   old freva systems to new ones.

> ``💡`` You can use the `-l` flag of the `deploy-freva cmd` command
or tick the *local deployment only* box in the setup page of the text user
interface if you only want to try out the deployment on your local machine.
Without having to install anything on remote machines.



## Installing docker/podman to the service servers
Because the services of MariaDB, DatabrowserAPI and Apache httpd will be deployed
on container images, docker or podman needs to be available on the target servers.
Since version *v2309.0.0* of the deployment the containers are set up
using `doker-compose` or `podman-compose`. The deployment will install,
`docker-compose` or `podman-compose` if not already available on the servers.


Hence, on the servers that will be running docker
you will need root access. There exists an option to install and run docker
without root, information on a root-less docker option
can be found [on the docker docs](https://docs.docker.com/engine/security/rootless/)
> ``💡`` The deployment will automatically check the availability of docker
or podman and chose the software that is available on each server.
