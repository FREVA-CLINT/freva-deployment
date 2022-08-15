# After successful deployment
## After deployment of the core
### Activation scripts and module files for users
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


## Solr, database and web services:
If the target machine where the services (solr, mariadb, web) were deployed
are Linux machines you will have access to a `systemd` unit of the created
service. In general the services can be accessed by
`<project_name>-<service_name>.service` If for example the `project_name`
key was set to `clex-ces` then the following services are created:

- database: `clex-ces-db.service`, `clex-ces-vault.serice`
- solr: `clex-ces.solr.service`
- web ui: `clex-ces-web.service`, `clex-ces-redis.service`, `clex-ces-httpd.service`

### Access of service data on the host machine
The data of the services, like the database or solr cores are stored "outside"
the docker containers on the host machine and can be accessed at
`/opt/freva/<project_name>/<service_name>_service/` for example
`/opt/freva/clex-ces/db_service`


### Simple backup scripts:
The `db` and `solr` services offer a very simple backup script that can
be run from outside the container. To issue a backup command simply call the
following command `docker/podman exec -it <project_name>-solr/db /usr/local/bin/daily_backup`.
For example:

```
podman exec -it clex-ces-solr /usr/local/bin/daily_backup
```

If you have `anacron` set up on your host machine then a cron script to
automatically backup databases and solr cores is applied nightly.
By default the script keeps the last 7 backups. Backup data can be found in:

- `db`:`/opt/freva/<project_name>/db_service>/backup`
- `solr`: `/opt/freva/<project_name>/solr_service/<core_name>/data/snapshot.YYYYMMDDHHMMSSMS`

This is only a rudimentary backup solution, ideally you should transfer those
backups regularly to a different location. You can also disable this
rudimentary backup strategy by deleting the backup scripts in `/etc/cron.daily`
and replace it by a more sophisticated backup mechanism.

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


### Adding privacy notes and terms of conditions to the Web UI
For some incitations it might be necessary to add legal statements on privacy
and terms of usage. Those statements can be added as flat-pages in the django
*admin* panel. All flat-pages starting with the url **/legal** for example
`/legal/privacy/` will be added as a link to the footer of home page. Examples
of the content of such flat-pages can be found in the [Appendix III](LegalNotes.html).
