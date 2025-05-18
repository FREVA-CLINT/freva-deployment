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

{{cli_mig}}

The `cert-file` positional argument refers to the public certificate file that was
created during the deployment process and is needed to establish a connection to
the new database (via the vault). You can either use the one that has been
saved by the deployment or use it from the freva config directory. By default
the certificate file resides within `freva` path of the deployment `root_dir`
for example `/mnt/project/freva/project.crt`. Also don't forget to set the domain
name for your institution as a unique identifier.

After the command has been applied the new database with its "old" content from
the previous Freva instance will be ready for use.


## Transition to new DRS Config

In the old version the DRS (Date Reference Syntax) File configuration,
that is the definitions of dataset metadata, was hard coded into the module
`evaluation_system.model.file`. In the new version this configuration
is saved in a designated [toml](https://toml.io/en/) file (drs_config.toml).
The ingestion of data is done by the new `data-crawler` software, which is
written in python. More information on this configuration and usage of the
software can be found on the [software documentation](https://freva.gitlab-pages.dkrz.de/metadata-crawler-source/docs/index.html).
