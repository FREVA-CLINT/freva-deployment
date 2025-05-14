# Activation scripts and module files for users
The core deployment will create activation scripts for various shell flavours.
The following activation scripts are located in the `<root_dir>/freva` folder:
* *activate_sh*: To be sourced by shell flavours like shell, bash, zsh etc.
* *activate_csh*: To be sourced by c-shell flavours like csh, tcsh
* *activate_fish*: To be source by fish
* *loadfreva.module*: Modules file
The source scripts can either be copied where they are automatically sourced
or users can be instructed to use the source command for their shell. If
`modules` is available on the host system you can copy the *loadfreva.modules*
file into the `MODULEPATH` location.


# Persisent micro service data:
If you chose podman/docker or conda based deployment of the micro-services
you will have access to a `systemd` unit of the created
service. In general the services can be accessed by
`<project_name>-<service_name>.service` If for example the `project_name`
key was set to `clex-ces` then the following services are created:

- database: `clex-ces-db.service`, `clex-ces-vault.serice`
- freva-rest: `clex-ces-freva-rest.service` `clex-ces-mongo.service`
- web ui: `clex-ces-web.service` `clex-ces-web-cache.service` `clex-ces-web-proxy.service`
- data-loader: `freva-caching.service` `data-loader@schduler.service` `data-loader@worker.service`

The data-loader services for zarr streaming are optional. Additionally
`clex-ces-web-cache.service` `clex-ces-web-proxy.service` will only be present
for *conda-forge* based deployments.

> ``💡`` If you have set up the services as an unprivileged user you need
to access the services with help of the ``--user`` flag for example:

```console
systemclt --user restart clex-ces-web.service
```

## Access of service data on the host machine

### Conda-forge base deployments
The data of the services, like the database or databrowser cores
should be persistent. The default location for all the service data
is `/opt/freva` or whatever folder was set as `data_path` variable.
The following logic applies:

- `<data_path>/<project_name>/services/<project_name>/<service_name>/`

for example:

- `/opt/freva/clex-ces/services/db/`

The conda environments are stored in:

- `<data_path>/<project_name>/conda`

for example:

- `/opt/freva/clex-ces/conda`

### Container based deployment
Persistent data for container based deployments in stored in docker/podman managed
volumes. The volume names follow the following structure:

`<project_name>-<service>_<name>`

for exmaple:
- `clex-ces-db_data`: Persistent database data
- `clex-ces-db_logs`: Persistent database logs

You can inspect the volumes using the following commands:

```console

podman volume ls
podman volume inspect <project_name>-<service>_<type>

```


If you chose the `docker/podman` deployment option then the containers are
orchestrated using `podman-compose` / `docker-compose`.
The compose files are also located in the `<data_path>/<project_name>/compose_services`
location, for example:

- `/opt/freva/clex-ces/compose_services`

## Simple backup scripts:
The `db` and `databrowser` services offer a very simple backup script.
Depending on the chosen setup mode this backup is either executed directly on the
host machine (conda-forge based deployment) or in a container.

If you have `anacron` set up on your host machine then a cron script to
automatically backup databases and solr cores is applied nightly.
By default the script keeps the last 7 backups. i
For conda-forge base deployments the backup data can be found in:

- `db`:`<data_path>/<project_name>/services/db/backup`
- `solr`: `<data_path><project_name>/services/solr/<core_name>/data/snapshot.YYYYMMDDHHMMSSMS`

Container deployments (docker/podman) utilise the following volumes:

- `db`: `<project_name>-db_backup`
- `solr`: `<project_name>-solr_data`

This is only a rudimentary backup solution, ideally you should transfer those
backups regularly to a different location. You can also disable this
rudimentary backup strategy by deleting the backup scripts in `/etc/cron.daily`
and replace it by a more sophisticated backup mechanism.


> ``💡`` If you have set up the services as an unprivileged user you can
access the backup scripts using the `crontab` command.

(the-web-ui-admin-panel)=
## The web UI admin Panel

The web user interface is manged by django which offers a powerful admin
panel to manage users, user history and add additional links as so called
flat pages. More information on the django admin panel can be found
[online](https://www.tutorialspoint.com/django/django_admin_interface.htm).
To access the admin panel you will first have to login as user `freva-admin`
using the *master* password you've created during deployment. Once logged in
as freva-admin you should navigate to `/admin` of your homepage. For example
`https://www.clex.nci.org.au/admin` assuming the web page url is
`https://www.clex.nci.org.au`. Here you can transfer admin rights to other
users, like your user name. Or create
[new flat-pages](https://docs.djangoproject.com/en/4.0/ref/contrib/flatpages/).
Flat-pages are useful to create additional project specific information that
can be displayed on the website. This information can be links to plugin
documentation or legal notes (see below).


## Adding privacy notes and terms of conditions to the Web UI
For some incitations it might be necessary to add legal statements on privacy
and terms of usage. Those statements can be added as flat-pages in the django
*admin* panel. All flat-pages starting with the url **/legal** for example
`/legal/privacy/` will be added as a link to the footer of home page. Examples
of the content of such flat-pages can be found in the [Appendix](LegalNotes).
