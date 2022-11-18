==========
Twister v2
==========

.. image:: https://github.com/zephyrproject-rtos/twister/actions/workflows/main.yaml/badge.svg?branch=main
   :target: https://github.com/zephyrproject-rtos/twister/actions?query=workflow?main
   :alt: Run tests
.. image:: https://codecov.io/gh/zephyrproject-rtos/twister/branch/main/graph/badge.svg?token=F8DSSX20B5
   :target: https://codecov.io/gh/zephyrproject-rtos/twister
   :alt: Code coverage

Pytest plugin to run Zephyr tests and collect results.

CAUTION
-------

This repository is not used in production and is still under development.
The code for Twister which is used in Zephyr's CIs can be found `here <https://github.com/zephyrproject-rtos/zephyr/blob/main/scripts/twister>`_.

Installation
------------

Installation from github:

.. code-block:: sh

  pip install git+https://github.com/zephyrproject-rtos/twister.git


Installation from the source:

.. code-block:: sh

  pip install .


Build wheel package:

.. code-block:: sh

  pip install build
  python -m build --wheel


Requirements
------------

* Python >= 3.8
* pytest >= 7.0.0


Usage
-----

Show all available options:

.. code-block:: sh

  pytest --help


Run tests:

.. code-block:: sh

  pytest <PATH_TO_ZEPHYR>/tests/kernel/common -vv --zephyr-base=<PATH_TO_ZEPHYR> --platform=native_posix --results-json=twister-out/results.json --log-level=DEBUG


If environmental variable ``ZEPHYR_BASE`` is set, one can omit ``--zephyr-base`` argument.

Show what fixtures and tests would be executed but don't execute anything:

.. code-block:: sh

  pytest tests --setup-plan


List all tests without executing:

.. code-block:: sh

  pytest tests --collect-only


Run tests only for specific platforms:

.. code-block:: sh

  pytest tests --platform=qemu_x86 --platform=nrf51dk_nrf51422


Provide directory to search for board configuration files:

.. code-block:: sh

  pytest tests --board-root=path_to_board_dir


Reports
-------

Generate test plan in JSON format:

.. code-block:: sh

  pytest tests --testplan-csv=testplan.csv --collect-only


Generate test plan in CSV format:

.. code-block:: sh

  pytest tests --testplan-json=testplan.json --collect-only


Generate test results in JSON format:

.. code-block:: sh

  pytest tests --resutls-json=results.json


Filtering tests
---------------

Run tests with given tags (`@` is optional and can be omitted):

.. code-block:: sh

  pytest tests --tags=@tag1,@tag2


Examples of usage:

* not tag1

  - `--tags=~@tag1`

* tag1 and tag2:

  - `--tags=@tag1 --tags=@tag2`

* tag1 or tag2

  - `--tags=@tag1,@tag2`

* (tag1 or tag2) and tag3 and not tag4

  - `--tags=@tag1,@tag2 --tags=@tag3 --tags=~@tag4`


Tools
-----

Scan connected devices and create hardware map:

.. code-block:: sh

  twister_tools --generate-hardware-map hardware_map.yaml


Scan connected devices and list hardware map:

.. code-block:: sh

  twister_tools --list-hardware-map


List default platforms:

.. code-block:: sh

  twister_tools --list-default-platforms
