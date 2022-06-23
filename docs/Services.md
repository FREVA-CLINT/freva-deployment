# Remote control of project services
This option only applies if you have installed a [service mapping](Installation.html#setting-up-a-service-that-maps-the-server-structure).
The installation routine saves the host names of the services for each project in
a central location. After the deployment the project services can be restarted,
stopped or started via the `freva-service` command.

```bash
freva-service --help
usage: freva-service [-h] [--server-map SERVER_MAP] [--services {web,db,solr} [{web,db,solr} ...]] [--user USER] [-v] [-V]
                     {start,stop,restart,status} [project_name]

Interact with installed Freva services.

positional arguments:
  {start,stop,restart,status}
                        The start|stop|restart|status command for the service
  project_name          Name of the project (default: all)

options:
  -h, --help            show this help message and exit
  --server-map SERVER_MAP
                        Hostname of the service mapping the Freva server architecture, Note: you can create a server map by running
                        the deploy-freva-map command (default: None)
  --services {web,db,solr} [{web,db,solr} ...]
                        The services to be started|stopped|restarted|checked (default: ['solr', 'db', 'web'])
  --user USER, -u USER  connect as this user (default: None)
  -v, --verbose         Verbosity level (default: 0)
  -V, --version         show program's version number and exit

```

The command takes two positional arguments. The first one instructs the
command whether the service should be started, stopped or restarted.
The second positional argument points to the project name. This is project name
that was used during deployment for example `clex`. Individual services
can be set by the `--services` option. By default all services (`db`, `web` and `solr`)
will be modified. The `--user` flag can be set if the login user name to the
target machine(s) differs from the current system user.

The below example restarts the apache solr service in the `clex` project:

```bash
freva-service restart clex --service solr --user k12345
```

> **_Note:_** All services (`db`, `web` and `solr`) will be selected if the `--services` option
is omitted.
