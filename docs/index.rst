.. freva-deployment documentation master file, created by
   sphinx-quickstart on Tue Mar  1 16:19:20 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to freva admin documentation!
=====================================

.. image:: freva_flowchart-new.jpg
   :width: 320
   :align: center

.. note::

    Please check :ref:`whatsnew` for any update announcments.



Freva, the free evaluation system framework, is a data search and analysis
platform developed by the atmospheric science community for the atmospheric
science community. With help of Freva researchers can:

- quickly and intuitively search for data stored at typical data centers that
  host many datasets.
- create a common interface for user defined data analysis tools.
- apply data analysis tools in a reproducible manner.

Data analysis is realised by user developed data analysis plugins. These plugins
are code agnostic, meaning that users don't have to rewrite the core of their
plugins to make them work with Freva. All that Freva does is providing a user
interface for the plugins.

Currently Freva comes in three different flavours:

- a python module that allows the usage of Freva in python environments, like
  jupyter notebooks
- a command line interface (cli) that allows using Freva from the command
  lines and shell scripts.
- a web user interface (web-ui)


This documentation gives an overview over the installation process of Freva
as well as it's configuration, maintenance and administration. It
mainly covers the deployment process and the usage of a dedicated deployment
software that was tailored to make the installation process of Freva somewhat
more simple.

Because Freva is a software that is meant to run on HPC type distributed systems
this documentation first gives an overview of various deployment strategies.
After this section a basic configuration that is necessary to make the different
components of Freva work with each other is introduced. This is followed by a
documentation on how to install the Freva deployment software. After this section
basic deployment setup and servicing Freva will be introduced.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   Architecture
   Folders
   Installation
   Configure
   AfterDeployment
   Services
   TuiHowto
   Transition
   LegalNotes
   modules
   whatsnew

Contributing to freva-deployment
================================

We welcome contributions from the community! Before you start contributing,
please follow these steps to set up your development environment.
Make sure you have the following prerequisites installed:

- Python (>=3.x)
- Git
- Make

.. code:: console

    git clone https://github.com/FREVA-CLINT/freva-deployment.git
    cd freva-deployment.git

Development Workflow
--------------------

We use a Makefile to manage common development tasks. Here are some useful
commands:


1. To install in development mode use:

.. code:: console

    make

2. To reformat and do type checking:

.. code:: console

    make lint

3. Generate the documentations:

.. code:: console

    make docs

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
