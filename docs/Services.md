# Remote control of project services
The installation routine saves the hosts of the services for each project in
as central location. After deployment the project services can be restarted,
stopped or started via the `freva-service` command.

```bash
usage: freva-service [-h] [--services {web,db,solr} [{web,db,solr} ...]] [--user USER]
                     {start,stop,restart} project_name

Interact with installed freva services.

positional arguments:
  {start,stop,restart}  The start|stop|restart command for the service
  project_name          Name of the project

options:
  -h, --help            show this help message and exit
  --services {web,db,solr} [{web,db,solr} ...]
                        The services to be started|stopped|restarted (default: ['solr', 'db', 'web'])
  --user USER, -u USER  connect as this user (default: None)
```

The command takes two positional arguments. The first one instructs the
command whether the service should be started, stopped or restarted.
The second positional argument points to the project name. This is project name
that was used during deployment for example `xces`. Individual services
can be set by the `--services` option. By default all services (`db`, `web` and `solr`)
will be modified. The `--user` flag can be set if the login user name to the
target machine(s) differs from the current system user.

The below example restarts the apache solr service in the `xces` project:

```bash
freva-service restart xces --service solr --user k12345
```
