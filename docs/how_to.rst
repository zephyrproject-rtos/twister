======
How-to
======

Use twister plugin with regular python tests
============================================

It is possible to use twister plugin with regular pytest tests to build a source code and run it on a device.

First, we have to create a folder (``hello_world``) which contains our tests.
In this folder we have ``hello_world_test.py`` file which contains code of our tests,
and ``testspec.yaml`` with a configuration to build scenarios. There is also ``src`` directory
with our C code which we want to build.

The folder structure can look like that:

.. code-block:: shell

    └── tests
        └── hello_world
            ├── CMakeLists.txt
            ├── hello_world_test.py
            ├── prj.conf
            ├── src
            │   └── main.c
            └── testspec.yaml


In the ``hello_world`` directory we have ``testspec.yaml`` file which
contains test specification. In this file ``scenario1``, ``scenario2`` and ``scenario3`` are our variants of build configurations.

.. code-block:: yaml
    :name: testspec.yaml

    common:
        timeout: 30
        harness: console
        harness_config:
            type: one_line
            regex:
                - "Hello World! (.*)"
    tests:
        scenario1:
            tags: introduction
        scenario2:
            tags: tag1
        scenario3:
            tags: tag2


Then we have tests implementation like so:

.. code-block:: python
   :name: hello_world_test.py

    # -- FILE: hello_world_test.py
    import re
    import pytest

    # it will generate variants for all available scenarios from yaml file
    @pytest.mark.build_specification
    def test_hello_world(build, log_parser):
        log_parser.parse(timeout=5)
        assert log_parser.state == 'PASSED'

    # it will generate variants for scenario1 and scenario2 only
    @pytest.mark.build_specification('scenario1', 'scenario2')
    def test_hello_world_2(build, dut):
        pattern = re.compile('.*Hello World.*')
        assert any(pattern.match(line) for line in dut.iter_stdout)


In the example above we use ``@pytest.mark.build_specification`` marker to inform ``pytest`` that these tests
have ``testspec.yaml`` with configuration for building source code.
Another fixture ``build`` is used to build the source code for our tests.
Fixture ``dut`` is used to run built code on a device. And last fixture ``log_parser`` is used
to parse output from a device and search for expected messages (defined as regex in ``testspec.yaml``)


If we run command to collect all tests:

.. code-block:: shell

    $ pytest tests --platform=native_posix --platform=nrf52840dk_nrf52840 --collect-only


We will get the following combinations:

.. code-block:: shell

    <Module tests/hello_world/hello_world_test.py>
        <Function test_hello_world[nrf52840dk_nrf52840:scenario1]>
        <Function test_hello_world[nrf52840dk_nrf52840:scenario2]>
        <Function test_hello_world[nrf52840dk_nrf52840:scenario3]>
        <Function test_hello_world[native_posix:scenario1]>
        <Function test_hello_world[native_posix:scenario2]>
        <Function test_hello_world[native_posix:scenario3]>
        <Function test_hello_world_2[nrf52840dk_nrf52840:scenario1]>
        <Function test_hello_world_2[nrf52840dk_nrf52840:scenario2]>
        <Function test_hello_world_2[native_posix:scenario1]>
        <Function test_hello_world_2[native_posix:scenario2]>
