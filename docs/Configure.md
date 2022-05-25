# Running and configuring the deployment
A complete freva instance will need the following services:

- solrservers (hostname of the apache solr server)
- dbservers (hostname of the MariaDB server)
- webservers (hostname that will host the web site)
- backendservers (hostname(s) where the command line interface will be installed)

## Setting the python and git path
Some systems do not have access to python3.6+ (/usr/bin/python3) or git by default.
In such cases you can overwrite the `ansible_python_interpreter` in the inventory
settings of the server section to point ansible to a custom `python3` bindary. For example

```
ansible_python_interpreter=/sw/spack-rhel6/miniforge3-4.9.2-3-Linux-x86_64-pwdbqi/bin/python3
```

The same applies to the path to the git binary:

```
git_path=/sw/spack-levante/git-2.31.1-25ve7r/bin/git
```
## A map of your server infrastructure
Different freva instances are installed across different server hosts. Usually
the different freva instances running at an institution are distinguished by
a unique project name associated with each freva instance for example `xces`.
To keep track of all server and services we have created a service that keeps
track of the locations of all services for certain freva instances.
*Before* the first deployment we recommend to setup this server map by issuing
the `deploy-freva-map` command. Please also refer to the [installation section](Installation.html#setting-up-a-service-that-maps-the-server-structure)
for more details.


## Running the deployment
After successful configuration you can run the deployment.
The command `deploy-freva` opens a text user interface (tui) that will walk
you through the setup of the deployment.
> **_Note:_** Navigation is similar to the one of the *nano* text editor. The shortcuts start with a `^` which indicates `CTRL+`.

### Deployment with existing configuration.
If you already have a configuration saved in a toml base inventory file you can
issue the `deploy-freva-cmd` command:

```bash
deploy-freva-cmd --help
usage: deploy-freva-cmd [-h] [--server-map SERVER_MAP] [--config CONFIG]
                        [--steps {services,web,core,db,solr,backup} [{services,web,core,db,solr,backup} ...]] [--ask-pass] [-v] [-V]

Deploy freva and its services on different machines.

options:
  -h, --help            show this help message and exit
  --server-map SERVER_MAP
                        Hostname of the service mapping the freva server archtiecture, Note: you can create a server map by running
                        the deploy-freva-map command (default: None)
  --config CONFIG, -c CONFIG
                        Path to ansible inventory file. (default: /home/wilfred/.config/freva/deployment/inventory.toml)
  --steps {services,web,core,db,solr,backup} [{services,web,core,db,solr,backup} ...]
                        The services/code stack to be deployed (default: ['services', 'web', 'core'])
  --ask-pass            Connect to server via ssh passwd instead of public key. (default: False)
  -v, --verbose         Verbosity level (default: 0)
  -V, --version         show program's version number and exit

```

The `--steps` flags can be used if not all services should be deployed.

If the target machine where the services (solr, mariadb, web) were deployed
is a Linux machine you will have a `systemd` unit service was created.

## Known Issues:
Below are possible solutions to some known issues:

#### SSH connection fails:

```python
fatal: [host.name]: FAILED! => {"msg": "Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support this.  Please add this host's fingerprint to your known_hosts file to manage this host."}
```
- This means that you've never logged on to the server. You can avoid this error message by simply logging on to the server for the first time.

#### Playbook complains about refused connections for the solr or db playbook

```python
fatal: [localhost]: FAILED! => {"changed": true, "cmd": "docker run --name \"test_ces_db\" -e MYSQL_ROOT_PASSWORD=\"T3st\" -p \"3306\":3306 -d docker.io/library/mariadb", "delta": "0:00:00.229695", "end": "2021-05-27 16:10:58.553280", "msg": "non-zero return code", "rc": 125, "start": "2021-05-27 16:10:58.323585", "stderr": "docker: Error response from daemon: driver failed programming external connectivity on endpoint test_ces_db (d106bf1fe310a2ae0e012685df5a897874c61870c5241f7a2af2c4ce461794c2): Error starting userland proxy: listen tcp4 0.0.0.0:3306: bind: address already in use.", "stderr_lines": ["docker: Error response from daemon: driver failed programming external connectivity on endpoint test_ces_db (d106bf1fe310a2ae0e012685df5a897874c61870c5241f7a2af2c4ce461794c2): Error starting userland proxy: listen tcp4 0.0.0.0:3306: bind: address already in use."], "stdout": "895ba35cdf5dcf2d4ec86997aedf0637bf4020f2e9d3e5775221966dcfb820a5", "stdout_lines": ["895ba35cdf5dcf2d4ec86997aedf0637bf4020f2e9d3e5775221966dcfb820a5"]}
```
- This means that there is already a service running on this port - in this case a local mariadb service. To avoid this error chose a different port in your `config/inventory` file.

#### Playbook cannot create database tables because connections fails

```python
fatal: [localhost]: FAILED! => {"changed": false, "msg": "ERROR 1698 (28000): Access denied for user 'root'@'localhost'\n"}
```
- This is a common problem if you've set the mariadb docker host to be localhost. You can avoid the problem by setting the `db_host` variable to a non localhost type IP like 172.17.0.1. If you're not sure what IP to use try the following command
```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db_docker_name
```
you can figure out the `db_docker_name` using the following command:
```
docker container ls
```

#### Git related unit tests in backend playbook fail
Git pull and push commands tend to fail if you haven't configured git. In this case change into the /tmp/evaluation_system directory of the host that runs the playbook
then manually trigger the unit tests by

```
FREVA_ENV=/path/to/root_dir make tests
```
You can then check the stderr for messages for git related issues. Usually it helps to configure git before hand:

```bash
git config --global init.defaultBranch main
git config --global user.name your_user
git config --global user.email your@email.com
```


## Advanced: Adjusting the playbook
Playbook templates and be found the in the `playbooks` directory. You can also add new variables to the playbook if they are present in the `config/inventory` file.
