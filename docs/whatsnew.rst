.. _whatsnew:

What's new
===========

.. toctree::
   :maxdepth: 0
   :titlesonly:

v2403.0.1
~~~~~~~~~
*  A new procedure to check the correct versions of all micro services has
   been added
*  Unprivileged users (non-root) can now also deploy the system with all
   services.
*  For better testing a setup script that create separate VM to deploy the
   micro services has been added.

v2309.0.0
~~~~~~~~~

* All containers are created with `docker-compose` or `podman-compose` in order to be able to successfully deploy
  the containers you will have to install `docker-compose` or `podman-compose` on
  the host machines running the containers.
* With v2309 comes a new configuration file. If you are using the tui please
  just load your old config file. The code will update this configuration file.
  If you are using the `deploy-freva-cmd` command you will not have to do anything.
  The code automatically update your config file to the new config file. A backup
  with the suffix (`.bck`) will be created.
