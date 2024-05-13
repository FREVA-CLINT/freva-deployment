The freva-deployment software
#############################

The `freva-deployment` software is used to deploy Freva in different computing environments.
The general strategy is to split the deployment into different steps, these are :
- Deploy database service
- Deploy a HashiCorp Vault service for storing and retrieving passwords and other sensitive data via docker (this step get automatically activated once the MariaDB service is set)
- Deploy the `DatabrowserAPI <https://github.com/FREVA-CLINT/databrowserAPI>`_ The databrowser API deployment consists of three parts:

  - The actual databrowser rest API
  - Apache solr search backend
  - Mongodb to store search statistics

- Deploy command line interface and python library (`freva <https://github.com/FREVA-CLINT/freva>`_)
- Deploy web front end (`freva_web <https://github.com/FREVA-CLINT/freva-web>`_)
  The web front end deployment is sub divided into three parts:

  - Deployment of the django web application
  - Deployment of a redis instance acting as database cache
  - Deployment as a apache httpd service as a reverse proxy server for connections from the client to the django web application.

.. note::

    The vault server is auto deployed once the database server is deployed.
    The vault centrally stores all passwords and other sensitive data.

.. toctree::
   :maxdepth: 2

   Installation
   Configure
   TuiHowto
   Config
   changelog
