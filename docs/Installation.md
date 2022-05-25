# Installing the freva-deployment

The freva deployment is used to deploy freva in different computing environments. The general strategy is to split the deployment into 4 different steps, these are :
- Deploy MariaDB service via docker
- Deploy a Hashicorp Vault service for storing and retrieving passwords and other sensitive data via docker (this step get automatically activated once the MariaDB service is set)
- Deploy Apache Solr service via docker
- Deploy command line interface backend ([evaluation_system](https://gitlab.dkrz.de/freva/evaluation_system))
- Deploy web front end ([freva_web](https://gitlab.dkrz.de/freva/freva_web))


> **_Note:_** A vault server is auto deployed once the mariadb server is deployed. The vault centrally stores all passwords and other sensitive data. During the deployment of the vault server a public key is generated which is used to open the vault. This public key will be saved in the `evaluation_system` backend root directory. Only if saved this key and the key in the vault match, secrets can be retrieved. Therefore it might be a good idea to deploy, the mariadb server (and with it the vault) and the `evaluation_system` backend togehter.

On *CentOS* python SELinux libraries need to be installed. If you choose to install ansible via the `install_ansible` you'll have to use `conda` to install libselinux for your CentOS version. For example : `conda install -c conda-forge  libselinux-cos7-x86_64`

## Pre-Requisites
The main work will be done by [ansible](https://docs.ansible.com/ansible/latest/index.html), hence some level of familiarity with ansible is advantagous.
Since we are using ansible we can use this deployment routine from a workstation computer (like a Mac-book). You do not need to run the depoyment on the machines where things get installed.
The only requirement is that you have to setup ansible and you can establish ssh connections to the servers.
### Preparation on windows based system (without wsl).
Currently ansible is not natively available on windows based systems. You can use the
unix runtime environment [cygwin](https://www.cygwin.com) to download and install the
needed software. Just follow the steps listed on the web page to setup
cygwin on your windows system. In order to be able to install the freva deployment
programm you'll first need to install the following packages via cygwin:

- python3
- python3-devel
- git
- make
- python3.X-paramiko
- libffi-devel
- ansible

We also recommend installing a command line based text editor like vim, nano, etc.

After installing the above listed packages via cygwin you can clone and install the freva deployment:

```bash
pip install (--user) git+https://gitlab.dkrz.de/freva/deployment.git
```
### Installation on \*nix systems or wsl.
If you're using Linux, OsX or a Windows subsystem for Linux (WSL) it should be sufficient to issues the following commands:

```bash
pip install (--user) ansible
pip install (--user) git+https://gitlab.dkrz.de/freva/deployment.git
```

This command installs ansible and all required python packages.
> **_Note:_** On *CentOS* python SELinux libraries need to be installed. You will need to install libselinux for your CentOS version.

```bash
python3 -m pip install (--user) libselinux-python3
```
## Installing docker/podman and sudo access to the service servers
Since the services of MariaDB, Apache Solr and Apache web will be deployed on docker container images, docker needs to be available on the target servers. Usually installing and running docker requires *root* privileges.
Hence, on the servers that will be running docker you will need root access.
There exist an option to install and run docker without root,
information on a root-less docker option
can be found [on the docker docs](https://docs.docker.com/engine/security/rootless/)
> **_Note:_** Some systems use `podman` instead of `docker`. The deployment
routine is able to distinguish and use the right service.

## Setting up a service that maps the server structure
Since the services might be scattered across different servers it might be hard
to keep track of the host names of the servers where all services are running.
We have created a service that keeps track of the locations of all services for
a certain freva instance. Although not strictly needed we recommend you to setup
this special server mapping service. To do so use the following command:

```bash
deploy-freva-map --help
usage: deploy-freva-map [-h] [--port PORT] [--wipe] [--user USER] [--python-path PYTHON_PATH] [-v] [-V] servername

Create service that maps the freva server architecture.

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
> **_Note_:** As the service keeps track of all freva instances within your institution, this has to be deployed only *once*. Please make sure that other admins who might need to install freva are aware of the host name for this service. *This step is optional*
