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


Installation the project in editable mode:

.. code-block:: sh

  pip install -e .


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


To use the plugin in a pytest run, simply add `--twister` to the command line invocation:

.. code-block:: sh

  pytest --twister ...


Run tests:

.. code-block:: sh

  pytest --twister <PATHS_TO_SCAN_FOR_TEST> -v --zephyr-base=<PATH_TO_ZEPHYR> --platform=native_posix --tb=no


``<PATHS_TO_SCAN_FOR_TEST>`` can be e.g. ``tests/kernel/common samples/hello_world``

If environmental variable ``ZEPHYR_BASE`` is set, one can omit ``--zephyr-base`` argument.

We advise here to use an extra pytest argument ``--tb=no``. It will turn off completely pytest traceback since it can be
very confusing for regular twister users.

Pytest by default captures any output sent to stdout and stderr and only prints it in case of a failure.
It can be disabled by adding ``-s`` argument. This allows seeing such output in real-time, e.g. an output printed
by a device under test and build logs in case of build failure.

A user can also set the logging level with ``--log-level``, e.g. ``--log-level=DEBUG``.

The verbosity level can be decreased by removing ``-v`` from the command and increased by adding an extra one.

* At verbosity level 0 only a testcase/sample.yaml currently executed will be printed and each test configuration inside will be marked with a green/red/yellow dot matching its status (pass/fail/skip)

* At verbosity level 1 each test configuration will be listed individually with corresponding written status.

* At verbosity level 2 matched ztest test cases from ztest test configurations will be additionally listed with their statuses (with ``SUB`` prefix, e.g. ``SUBPASS``, to distinguish from "full" tests)

Other usefull commands:

Parallelization of test execution is supported thanks to the xdist plugin. It can be turned on by adding ``-n auto`` to the command.
``auto`` can be replaced with integers telling explicitly how many workers to spawn.

Show what fixtures and tests would be executed but don't execute anything:

.. code-block:: sh

  pytest --twister tests --setup-plan


List all tests without executing:

.. code-block:: sh

  pytest --twister tests --collect-only


Run tests only for specific platforms:

.. code-block:: sh

  pytest --twister tests --platform=native_posix --platform=nrf52840dk_nrf52840


Provide directory to search for board configuration files:

.. code-block:: sh

  pytest --twister tests --board-root=path_to_board_dir


Reports
-------

Generate test plan in CSV format:

.. code-block:: sh

  pytest --twister tests --testplan-csv=testplan.csv --collect-only


Use custom path for test plan in JSON format:

.. code-block:: sh

  pytest --twister tests --testplan-json=custom_plan.json --collect-only


Use custom path for result report in JSON format:

.. code-block:: sh

  pytest --twister tests --resutls-json=custom_name.json


Filtering tests
---------------

Run tests with given tags (`@` is optional and can be omitted):

.. code-block:: sh

  pytest --twister tests --tags=@tag1,@tag2


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


List all platforms:

.. code-block:: sh

  twister_tools --list-platforms


List default platforms only:

.. code-block:: sh

  twister_tools --list-platforms --default-only

WARNING
-------

Our plugin requires pytest-subtest plugin, however, we modify the behavior of "subtests" introduced with this plugin.
The original implementation is based on subtest concept from unittest framework where such items are counted and reported
in a peculiar way.

The fact that we modify the behavior of subtests in our plugin can influence users who are using unittest-based subtests in other
projects. After adding our plugin to their existing environment the reporting of their existing subtests can change. To mitigate such issues
we recommend running different projects in different virtual environments.

Additional context: Twister defines 2 levels of "test items":

* test suites (configurations) that correspond to built test applications

* test cases that correspond to individual ztest test cases within test applications using ztest framework.

In our plugin, we modified the reporting and counting of subtests to match how twister is doing it. Test suites
are "tests" in pytest nomenclature and ztest test cases are based on subtests but they don't follow original unittest rules.
E.g. in unittest, when a subtest fails it is counted towards failing tests but when it passes it is not counted towards tests.
In our implementation, tests, and subtests have their own counters. I.e. subtests counts are not "leaking" into tests counts.
