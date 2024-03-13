# Installing freva-deployment
This section gives an overview over how to install the deployment software for
freva.

## Pre-Requisites
The main work will be done by [ansible](https://docs.ansible.com/ansible/latest/index.html),
hence some level of familiarity with ansible is advantageous but not necessary.
Since we are using ansible we can use this deployment routine from any workstation
computer (like a Mac-book). You do not need to run the deployment on the
machines where things get installed. The only requirement is that you have to
setup ansible and you can establish ssh connections to the servers.
### Preparation on windows based system (without wsl).
Currently ansible is not natively available on windows based systems. You can use the
unix runtime environment [cygwin](https://www.cygwin.com) to download and install the
needed software. Just follow the steps listed on the web page to setup
cygwin on your windows system. In order to be able to install the freva-deployment
program you'll first need to install the following packages via cygwin:

- python3
- python3-devel
- git
- make
- python3.X-paramiko
- libffi-devel
- ansible

We also recommend installing a command line based text editor like vim, nano, etc.

After installing the above listed packages via cygwin you can install the freva-deployment:

```console
python3 -m pip install -U freva-deployment
```
### Installation on \*nix systems or wsl.
If you're using Linux, OsX or a Windows subsystem for Linux (WSL) it should be
sufficient to issues the following commands:

```console
python3 -m pip install -U freva-deployment
```

This command installs ansible and all required python packages.
> **_Note:_** On *CentOS* python SELinux libraries need to be installed.
> You will need to install libselinux for your CentOS version.

```console
python3 -m pip install libselinux-python3
```

## Commands after installation:
The `pip install` command will create *four* different commands:
- `deploy-freva`: Text user interface to configure and run the deployment.
- `deploy-freva-cmd`: Run already configured deployment.
- `freva-migrate`: Command line interface to manage project migration from
   old freva systems to new ones.
If you can't find the commands mentioned above pip was probably installing
them in the user space. In that case you need to append your `PATH`
environment variable by `~/.local/bin`. If you use bash for example, add
the following command to your local `.bashrc`:

```console
export PATH=$PATH:$HOME/.local/bin
```
> **_Note:_** You can use the `-l` flag of the `deploy-freva-cmd` command
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
l need root access. There exists an option to install and run docker
without root, information on a root-less docker option
can be found [on the docker docs](https://docs.docker.com/engine/security/rootless/)
> **_Note:_** The deployment will automatically check the availability of docker
or podman and chose the software that is available on each server.
