# Transitioning guide

The following serves as a guide to transition an existing Freva instance
(within the python*2* frame work) to the new (python*3* based) version.


## Transition to new Database
We have created a small command line interface (`deploy-freva migrate`) that
helps migrating content of an existing Freva framework to the new one.
The `deploy-freva migrate` sub command has currently one sub commands:

The new system has witnessed small changes to the database structure. The `database`
sub-command of the `deploy-freva migrate` sub command helps to transition to this new
database structure. To migrate a database of an old installation of the Freva
system to a freshly deployed Freva instance use the following command:

```
usage: deploy-freva migrate database [-h] [--old-port OLD_PORT] [--old-db OLD_DB] [--old-pw OLD_PW] [--old-user OLD_USER]
                              new_hostname old_hostname cert-file

Freva database migration

positional arguments:
  new_hostname         The hostname where the new database is deployed.
  old_hostname         Hostname of the old database.
  cert-file            Path to the public certificate file.

options:
  -h, --help           show this help message and exit
  --old-port OLD_PORT  The port where the old database server is running on. (default: 3306)
  --old-db OLD_DB      The name of the old database (default: evaluationsystem)
  --old-pw OLD_PW      The passowrd to the old database (default: None)
  --old-user OLD_USER  The old database user (default: evaluationsystem)
```

The `cert-file` positional argument refers to the public certificate file that was
created during the deployment process and is needed to establish a connection to
the new database (via the vault). You can either use the one that has been
saved by the deployment or use it from the freva config directory. By default
the certificate file resides within `freva` path of the deployment `root_dir`
for example `/mnt/project/freva/project.crt`. Also don't forget to set the domain
name for your institution as a unique identifier.

After the command has been applied the new database with its "old" content from
the previous Freva instance will be ready for use.

> ``💡`` The migrate database sub command uses `mysqldump`. This program needs
> to be available on your system. Please make sure that it is installed.

## Transition to new DRS Config

In the old version the DRS (Date Reference Syntax) File configuration,
that is the definitions of dataset metadata, was hard coded into the module
`evaluation_system.model.file`. In the new version this configuration
is saved in a designated [toml](https://toml.io/en/) file (drs_config.toml).
The ingestion of data is done by the new `data-crawler` software, which is
written in python. More information on this configuration and usage of the
software can be found on the [software documentation](https://freva.gitlab-pages.dkrz.de/metadata-crawler-source/docs/index.html).
