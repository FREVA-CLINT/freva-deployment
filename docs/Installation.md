# Installing the freva-deployment

The freva-deployment is used to deploy Freva in different computing environments.
The general strategy is to split the deployment into different steps, these are :
- Deploy MariaDB service via docker
- Deploy a HashiCorp Vault service for storing and retrieving passwords and other sensitive data via docker (this step get automatically activated once the MariaDB service is set)
- Deploy Apache Solr service via docker
- Deploy command line interface backend ([evaluation_system](https://github.com/FREVA-CLINT/freva))
- Deploy web front end ([freva_web](https://gitlab.dkrz.de/freva/freva_web))
  The web front end deployment is sub divided into three parts:
    - Deployment of the django web application
    - Deployment of a redis instance acting as database cache
    - Deployment as a apache httpd service as a reverse proxy server for connections
      from the client to the django web application.

> **_Note:_** The vault server is auto deployed once the mariadb server is deployed.
The vault centrally stores all passwords and other sensitive data.

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

After installing the above listed packages via cygwin you can clone and install the freva-deployment:

```console
python3 pip install -U freva-deployment
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
- `deploy-freva-map`: To setup a service that keeps track of all deployed
   freva instances and their services.
- `deploy-freva`: Text user interface to configure and run the deployment.
- `deploy-freva-cmd`: Run already configured deployment.
- `freva-service`: Start|Stop|Restart|Check services of freva instances.
- `freva-migrate`: Command line interface to manage project migration from
   old freva systems to new ones.
If you can't find the commands mentioned above pip was probably installing
them in the user space. In that case you need to append your `PATH`
environment variable by `~/.local/bin`. If you use bash for example, add
the following command to your local `.bashrc`:

```console
export PATH=$PATH:$HOME/.local/bin
```


## Installing docker/podman and sudo access to the service servers
Since the services of MariaDB, Apache Solr and Apache httpd will be deployed on
docker container images, docker needs to be available on the target servers.
Usually installing and running docker requires *root* privileges.
Hence, on the servers that will be running docker you will need root access.
There exists an option to install and run docker without root,
information on a root-less docker option
can be found [on the docker docs](https://docs.docker.com/engine/security/rootless/)
> **_Note:_** Some systems use `podman` instead of `docker`. The deployment
routine is able to distinguish and use the right service.

## Setting up a service that maps the server structure (optional)
Since the services might be scattered across different servers it might be hard
to keep track of the host names of the servers where all services are running.
We have created a small service that keeps track of the locations of all services
for *all* Freva instance within your.
Although not strictly needed we recommend you to setup this special server
mapping service. To do so use the following command:

```console
deploy-freva-map --help
usage: deploy-freva-map [-h] [--port PORT] [--wipe] [--user USER] [--python-path PYTHON_PATH] [-v] [-V] servername

Create service that maps the Freva server architecture.

positional arguments:
  servername            The server name where the infrastructure mapping service is deployed

options:
  -h, --help            show this help message and exit
  --port PORT           The port the service is listing to (default: 6111)
  --wipe                Delete any existing data. (default: False)
  --user USER           Username to log on to the target server. (default: None)
  --python-path PYTHON_PATH
                        Path to the default python3 interpreter on the target machine. (default: /usr/bin/python)
  -v, --verbose         Verbosity level (default: 0)
  -V, --version         show program's version number and exit
```
> **_Note_:** As the service keeps track of all Freva instances within your
institution, this has to be deployed only *once*. Please make sure that other
admins who might need to install Freva are aware of the host name for this service.
*This step is optional*
