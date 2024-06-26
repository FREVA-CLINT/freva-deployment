# Example deployment configuration

This section contains two working versions of a full deployment configuration.
These configuration files have also been installed along with the deployment.
You can find them in the data files under `share/freva/deployment/config` of your
python environment, for example:
 - `/usr/share/freva/deployment/config` for system wide installations.
 - `$CONDA_PREFIX/share/freva/deployment/config` for conda based installations.
 - `~/.local/share/freva/deployment/config` for user based installations.

 ## Typical deployment
 The `inventory.toml` file contains a typical setup for freva. The services
 are installed with root privileges on remote machines. The core is installed
 under a normal user on a login node of a HPC system.

 ```toml
# This is the "default" freva deployment configuration file.
#
#   - The files syntax follows the `toml` markup language (https://toml.io)
#   - Comments begin with the "#" character
#   - Blank lines are ignored
#   - Groups of hosts are delimited by [header] elements
#   - The groups define different deployment steps
#   - Additional configuration for each group is set in the config section
#     of each header -> [header.config]
#   - You can enter host names or IP addresses
#   - A host name/IP can be a member of multiple groups


## The first part of this configuration defines general configuration that
## is common among all deployment steps.

# The project name that should be used for this freva instance
# NOTE: this key has to be the first in the file
project_name = "freva"

## Set the path to the SSL certificate files that is used to make password
## queries to the vault server or used as web certificates.
[certificates]

## Path to the public key file
public_keyfile = ""

## Path to the private key file
privat_keyfile = ""

## Path to the chain file
chain_keyfile = ""



[web]
# Set the host names where all services web UI will be deployed
hosts = "localhost"

# If you have multiple hosts following a pattern you can specify
# them like this:

## hosts = "alpha.example.org,beta.example.org,192.168.1.100,192.168.1.110"
## hosts = "www[001:006].example.com"

## Ex : A collection of database servers in the "dbservers" group

## Here"s another example of host ranges, this time there are no
## leading 0s:

## hosts = "db-[99:101]-node.example.com"
[databrowser]
## Set the host names running the databrowser service
hosts = "localhost"

[db]
## Set the host names running the mariadb service
hosts = "localhost"

[core]
### Set the host names where the command line interface of freva will be installed
hosts = "localhost"


### CONFIGURATION VARIABLES
##The following section defines important variables, which have to be set
##in order to deploy the system correctly
##
[db.config]

## Config variables for the database service
port = 3306
user = "freva"
db = "frevadb"

##If you need a different user name you can set it here (defaults to current user):
ansible_user = ""

## You can set the db_host separately, if none is given (default)
## the one from the hosts names above are taken

db_host = ""

## Set the become (sudo) user name to change to for installing the services
## leave blank to utilise a non privileged user based installation
ansible_become_user = "root"

## Ansible needs a python3 interpreter, which can be set for custom python3 instances
ansible_python_interpreter = ""

##Indicate whether or not to empty any pre-existing folders/docker volumes.
##(Useful for a truly fresh start) (default: False)
wipe = false

## Set the path where the permanent database data should be stored. By default
## this is set to /opt/freva/<project_name>/db_service
data_path = "/opt/freva"

## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
db_playbook = ""
vault_playbook = ""

[databrowser.config]
# Set the memory for the solr server (solr is the search engine in the background)
solr_mem = "4g"

# Set the port the databrowser should be running on
databrowser_port = 7777

## Set the become (sudo) user name to change to for installing the services
## leave blank to utilise a non privileged user based installation
ansible_become_user = "root"

## Ansible needs a python3 interpreter, which can be set for custom python3 instances

ansible_python_interpreter = ""

## If you need a different user name you can set it here (default to current user):
ansible_user = ""

##Indicate whether or not to empty any pre-existing folders/docker volumes.
##(Useful for a truly fresh start) (default: False)
wipe = false

## Set the path where the permanent databrowser data should be stored.
## By default this is set to /opt/freva
data_path = "/opt/freva"

## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
databrowser_playbook = ""



[core.config]
## List of user(s) that can alter the configuration of the freva cmd line interface
## If blank, the user that runs the deployment is chosen
admins = ""

## The path where the core should be installed
install_dir="~/freva-env"

## Set the path to any existing conda executable on the target machine,
## if not existing (default) a temporary conda distribution will be downloaded
conda_exec_path=""

## The directory where the project configuration files will be stored.
## This can be useful if you want to set up multiple freva instances with
## the same software stack. leave blank to use the same directory as
## `install_dir`
root_dir = ""

## If you which not to install a core instance but only configure one set the
## install variable to false. This can be useful if you have a central instance
## of freva deployed and want to setup a project specific configuration that
## uses this central instance
install = true

## The directory where the user specific output will be stored,
## if left blank then it defaults to `root_dir/work`
base_dir_location = ""

## Set the directory holding the user content, like plots, for the web user
## interface. Note: after plugin application, display content of the plugin
## output will be copied to this directory. The default location of this
## directory (if left value left blank) is ${base_dir_location}/share/preview
preview_path = ""

## Set the workload manager system, currently available are:
## "local", "slurm", "pbs", "lfs", "moab", "oar", "sge"
scheduler_system = "local"

## Set the path to the directory that contains the stdout of the plugins,
## this directory must be accessible to the web UI. The workload manager
## will write the stdout into this directory. Defaults to ${base_dir_location}/share
scheduler_output_dir = ""

# Set the target architecture of the system where the backend will be installed
# to. You can choose from the following options:
# Linux-x86_64 (default), Linux-aarch64, Linux-ppc64le, Linux-s390x, MacOSX-x86_64
arch = "Linux-x86_64"

## If you need to install the core or its configuration as a different user you can
## set the ansible_become_user variable, this will install the core as a
## different user. Leave blank for if not needed.
ansible_become_user = ""

##If you need a different user name you can set it here (defaults to current user):
ansible_user = ""

## Ansible needs a python3 interpreter, which can be set for custom python3 instances
ansible_python_interpreter = ""

## The core deployment needs git, if git is not in the default PATH variable
## you can set the path to the git executable
git_path = "/usr/bin/git"

## If you want to set special group rights for freva configuration files
## you can set the admin_group variable. If `admin_group` is set then config
## files and directories in the `base_dir_location` are only writable to
## `admin_group`
admin_grup = ""

##Indicate whether or not to empty any pre-existing folders/docker volumes.
##(Useful for a truly fresh start) (default: False)
wipe = false

## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
core_playbook = ""

[web.config]
## List of user that can alter the configuration of freva web
project_website = "www.freva.dkrz.de"

## Ansible needs a python3 interpreter, which can be set for custom python3 instances
ansible_python_interpreter = ""

##If you need a different user name you can set it here (defaults to current user):
ansible_user = ""

## Set the path where the permanent web data should be stored. By default
## this is set to /opt/freva
data_path = "/opt/freva"

##Set html colors
main_color = "Tomato"
border_color = "#6c2e1f"
hover_color = "#d0513a"

## The about us text is a small blurb about freva within the project
about_us_text = ""

## Set the path to the institution logo, this should be the path to the logo
## seen by the target system - make sure that this path exists on the target
## machine
institution_logo = ""

## Set an email addresses acting as contact point for users
contacts = ""

## Set the smpt email server that will be used to send emails to contacts via the web UI
email_host = ""

## Now set postal address
imprint = "Project name, German Climate Computing Centre (DKRZ), Bundesstr. 45a, 20146 Hamburg, Germany."

## Here you can set a lengthy project description.
## You can also set a path to a filename that contains the information.
## Instead of text you can set a path to a file containing the text, like a html file.
homepage_text = "Bal bla bla."

## Set a one line blurb of the project
homepage_heading = "Short description of the project."

## Set the name of the project/institution
institution_name = "Freva"

## Set the slurm scheduler host
scheduler_host = ["localhost"]

## Settings for ldap

## Ldap server name(s)
auth_ldap_server_uri = ""

## Set the group that will be allowed to log on
allowed_group = "test_group"

## Set the ldap search user base
ldap_user_base = "cn=users,cn=accounts,dc=dkrz,dc=de"

## Set the ldap search group base, note: do not add the allowed_group as it will be auto added
ldap_group_base = "cn=groups,cn=accounts,dc=dkrz,dc=de"

## distinguished name (dn) for the ldap user
ldap_user_dn = ""

## use encrypted ldap connection (needs to be configured)
auth_ldap_start_tls = false

## Set ldap last name search key
ldap_last_name_field = "givenname"

## Set ldap first name search key
ldap_first_name_field = "sn"

## Set ldap email search key
ldap_email_name_field = "mail"

## Set the ldap group class name
ldap_group_class = "groupOfNames"

## Set the ldap group type, available values are are [posix, nested]
ldap_group_type = "nested"

## Set the ldap tools class for users
ldap_model = "MiklipUserInformation"

## set the passwd for the ldap user
ldap_user_pw = ""

#######
## Set the hosts that are allowed to execute wsgi code
allowed_hosts = ["localhost"]

## Turn on/off debug mode on the website
debug=false

## Which plugin id should be used for the web tour
guest_tour_result = 105

## Set the menu entries
# Menu entries consist of three entries these are:
# [Label, url, html_id] -> e.g Plugins, plugins:home, plugin_menu
menu_entries = [["Data-Browser", "solr:data_browser","browser_menu"],
                ["Plugins","plugins:home", "plugin_menu"],
                ["History","history:history","history_menu"],
                ["Result-Browser", "history:result_browser","result_browser_menu"],
                ["Help", "plugins:about","doc_menu"]]
## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
web_playbook = ""

## Set the become (sudo) user name to change to for installing the services
## leave blank to utilise a non privileged user based installation
ansible_become_user = "root"
 ```


## Deployment with non-root privileges
The `unprivileged-user.toml` file contains a configuration that can be used
when root access is either off limits or undesired:

```toml
# This is the "default" freva deployment configuration file.
#
#   - The files syntax follows the `toml` markup language (https://toml.io)
#   - Comments begin with the "#" character
#   - Blank lines are ignored
#   - Groups of hosts are delimited by [header] elements
#   - The groups define different deployment steps
#   - Additional configuration for each group is set in the config section
#     of each header -> [header.config]
#   - You can enter host names or IP addresses
#   - A host name/IP can be a member of multiple groups


## The first part of this configuration defines general configuration that
## is common among all deployment steps.

# The project name that should be used for this freva instance
# NOTE: this key has to be the first in the file
project_name = "freva-local"

## Set the path to the SSL certificate files that is used to make password
## queries to the vault server or used as web certificates.
[certificates]

## Path to the public key file
public_keyfile = ""

## Path to the private key file
privat_keyfile = ""

## Path to the chain file
chain_keyfile = ""



[web]
# Set the host names where all services web UI will be deployed
hosts = "localhost"

# If you have multiple hosts following a pattern you can specify
# them like this:

## hosts = "alpha.example.org,beta.example.org,192.168.1.100,192.168.1.110"
## hosts = "www[001:006].example.com"

## Ex : A collection of database servers in the "dbservers" group

## Here"s another example of host ranges, this time there are no
## leading 0s:

## hosts = "db-[99:101]-node.example.com"
[databrowser]
## Set the host names running the databrowser service
hosts = "localhost"

[db]
## Set the host names running the mariadb service
hosts = "localhost"

[core]
### Set the host names where the command line interface of freva will be installed
hosts = "localhost"


### CONFIGURATION VARIABLES
##The following section defines important variables, which have to be set
##in order to deploy the system correctly
##
[db.config]

## Config variables for the database service
port = 3306
user = "freva"
db = "frevadb"

##If you need a different user name you can set it here (defaults to current user):
ansible_user = ""

## You can set the db_host separately, if none is given (default)
## the one from the hosts names above are taken

db_host = ""

## Set the become (sudo) user name to change to for installing the services
## leave blank to utilise a non privileged user based installation
ansible_become_user = ""

## Ansible needs a python3 interpreter, which can be set for custom python3 instances
ansible_python_interpreter = ""

##Indicate whether or not to empty any pre-existing folders/docker volumes.
##(Useful for a truly fresh start) (default: False)
wipe = false

## Set the path where the permanent database data should be stored. By default
## this is set to /opt/freva/<project_name>/db_service
data_path = "~/freva-local/services"

## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
db_playbook = ""
vault_playbook = ""

[databrowser.config]
# Set the memory for the solr server (solr is the search engine in the background)
solr_mem = "4g"

# Set the port the databrowser should be running on
databrowser_port = 7777

## Set the become (sudo) user name to change to for installing the services
## leave blank to utilise a non privileged user based installation
ansible_become_user = ""

## Ansible needs a python3 interpreter, which can be set for custom python3 instances

ansible_python_interpreter = ""

## If you need a different user name you can set it here (default to current user):
ansible_user = ""

##Indicate whether or not to empty any pre-existing folders/docker volumes.
##(Useful for a truly fresh start) (default: False)
wipe = false

## Set the path where the permanent databrowser data should be stored.
## By default this is set to /opt/freva
data_path = "~/freva-local/services"

## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
databrowser_playbook = ""



[core.config]
## List of user(s) that can alter the configuration of the freva cmd line interface
## If blank, the user that runs the deployment is chosen
admins = ""

## The path where the core should be installed
install_dir="~/freva-local"

## Set the path to any existing conda executable on the target machine,
## if not existing (default) a temporary conda distribution will be downloaded
conda_exec_path=""

## The directory where the project configuration files will be stored.
## This can be useful if you want to set up multiple freva instances with
## the same software stack. leave blank to use the same directory as
## `install_dir`
root_dir = ""

## If you which not to install a core instance but only configure one set the
## install variable to false. This can be useful if you have a central instance
## of freva deployed and want to setup a project specific configuration that
## uses this central instance
install = true

## The directory where the user specific output will be stored,
## if left blank then it defaults to `root_dir/work`
base_dir_location = ""

## Set the directory holding the user content, like plots, for the web user
## interface. Note: after plugin application, display content of the plugin
## output will be copied to this directory. The default location of this
## directory (if left value left blank) is ${base_dir_location}/share/preview
preview_path = ""

## Set the workload manager system, currently available are:
## "local", "slurm", "pbs", "lfs", "moab", "oar", "sge"
scheduler_system = "local"

## Set the path to the directory that contains the stdout of the plugins,
## this directory must be accessible to the web UI. The workload manager
## will write the stdout into this directory. Defaults to ${base_dir_location}/share
scheduler_output_dir = ""

# Set the target architecture of the system where the backend will be installed
# to. You can choose from the following options:
# Linux-x86_64 (default), Linux-aarch64, Linux-ppc64le, Linux-s390x, MacOSX-x86_64
arch = "Linux-x86_64"

## If you need to install the core or its configuration as a different user you can
## set the ansible_become_user variable, this will install the core as a
## different user. Leave blank for if not needed.
ansible_become_user = ""

##If you need a different user name you can set it here (defaults to current user):
ansible_user = ""

## Ansible needs a python3 interpreter, which can be set for custom python3 instances
ansible_python_interpreter = ""

## The core deployment needs git, if git is not in the default PATH variable
## you can set the path to the git executable
git_path = "/usr/bin/git"

## If you want to set special group rights for freva configuration files
## you can set the admin_group variable. If `admin_group` is set then config
## files and directories in the `base_dir_location` are only writable to
## `admin_group`
admin_grup = ""

##Indicate whether or not to empty any pre-existing folders/docker volumes.
##(Useful for a truly fresh start) (default: False)
wipe = false

## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
core_playbook = ""

[web.config]
## List of user that can alter the configuration of freva web
project_website = "www.freva.dkrz.de"

## Ansible needs a python3 interpreter, which can be set for custom python3 instances
ansible_python_interpreter = ""

##If you need a different user name you can set it here (defaults to current user):
ansible_user = ""

## Set the path where the permanent web data should be stored. By default
## this is set to /opt/freva
data_path = "~/freva-local/services"

##Set html colors
main_color = "Tomato"
border_color = "#6c2e1f"
hover_color = "#d0513a"

## The about us text is a small blurb about freva within the project
about_us_text = ""

## Set the path to the institution logo, this should be the path to the logo
## seen by the target system - make sure that this path exists on the target
## machine
institution_logo = ""

## Set an email addresses acting as contact point for users
contacts = ""

## Set the smpt email server that will be used to send emails to contacts via the web UI
email_host = ""

## Now set postal address
imprint = "Project name, German Climate Computing Centre (DKRZ), Bundesstr. 45a, 20146 Hamburg, Germany."

## Here you can set a lengthy project description.
## You can also set a path to a filename that contains the information.
## Instead of text you can set a path to a file containing the text, like a html file.
homepage_text = "Bal bla bla."

## Set a one line blurb of the project
homepage_heading = "Short description of the project."

## Set the name of the project/institution
institution_name = "Freva"

## Set the slurm scheduler host
scheduler_host = ["localhost"]

## Settings for ldap

## Ldap server name(s)
auth_ldap_server_uri = ""

## Set the group that will be allowed to log on
allowed_group = "test_group"

## Set the ldap search user base
ldap_user_base = "cn=users,cn=accounts,dc=dkrz,dc=de"

## Set the ldap search group base, note: do not add the allowed_group as it will be auto added
ldap_group_base = "cn=groups,cn=accounts,dc=dkrz,dc=de"

## distinguished name (dn) for the ldap user
ldap_user_dn = ""

## use encrypted ldap connection (needs to be configured)
auth_ldap_start_tls = false

## Set ldap last name search key
ldap_last_name_field = "givenname"

## Set ldap first name search key
ldap_first_name_field = "sn"

## Set ldap email search key
ldap_email_name_field = "mail"

## Set the ldap group class name
ldap_group_class = "groupOfNames"

## Set the ldap group type, available values are are [posix, nested]
ldap_group_type = "nested"

## Set the ldap tools class for users
ldap_model = "MiklipUserInformation"

## set the passwd for the ldap user
ldap_user_pw = ""

#######
## Set the hosts that are allowed to execute wsgi code
allowed_hosts = ["localhost"]

## Turn on/off debug mode on the website
debug=false

## Which plugin id should be used for the web tour
guest_tour_result = 105

## Set the menu entries
# Menu entries consist of three entries these are:
# [Label, url, html_id] -> e.g Plugins, plugins:home, plugin_menu
menu_entries = [["Data-Browser", "solr:data_browser","browser_menu"],
                ["Plugins","plugins:home", "plugin_menu"],
                ["History","history:history","history_menu"],
                ["Result-Browser", "history:result_browser","result_browser_menu"],
                ["Help", "plugins:about","doc_menu"]]
## In case you want to set a custom path to a ansible playbook,
## you can do this here, by default the deployment will use the playbook
## located in the user config directory.
## NOTE: only adjust this if you know what you are doing, if you leave this
## blank the system will used the default playbook (standard procedure)
web_playbook = ""

## Set the become (sudo) user name to change to for installing the services
## leave blank to utilise a non privileged user based installation
ansible_become_user = ""
```
