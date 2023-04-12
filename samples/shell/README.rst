.. _testing_shell_sample:

Testing shell
#############

Overview
********

This sample demonstrates how a pytest test can be created based on an already existing Zephyr application:
a sample for the `shell module <https://github.com/zephyrproject-rtos/zephyr/tree/main/samples/subsys/shell/shell_module>`_.
It also presents how a pytest test can communicate with an application through DUT's (device under test) interfaces and verify it's output.

**This example is not ment to be a torough test of the shell sample**.

Building and Running
********************
*A checkouted Zephyr repository is needed to execute this sample.*


* | Call :code:`pytest --twister` pointing to this directory and selecting platforms to use, the same way as for regular tests. E.g., from the twisterV2 directory:
  | :code:`pytest --twister samples/shell --zephyr-base=~/zephyrproject/zephyr --platform=qemu_x86 -v`.
  | To get more descriptive output and see exchanged messages add :code:`-s --log-level=INFO` to the call.


**Alternative approach (more direct integration with existing sources)**


#. Copy the source file of the test (*shell_test.py*) into a directory with the shell module sample (*zephyr/samples/subsys/shell/shell_module*).
#. In the same directory, change the name of *sample.yaml* to *testspec.yaml*.
#. In the *testspec.yaml* remove a line with *harness: keyboard* from *sample.shell.shell_module* entry.
#. | Call :code:`pytest --twister` pointing to the directory with the test and selecting platforms to use, the same way as for regular tests. E.g., from the Zephyr's directory:
   | :code:`pytest --twister samples/subsys/shell/shell_module --zephyr-base=~/zephyrproject/zephyr --platform=qemu_x86 -v`.
   | To get more descriptive output and see exchanged messages add :code:`-s --log-level=INFO` to the call.

Detailed explanation
********************

* | Tests in pytest using twister plugin are looking for *testspec.yaml* files. Such file can contain
  | *source_dir* entry pointing to Zephyr directory with application sources. In such case, content
  | of *sample/testcase.yaml* located there will be ignored.

* | Twister detects *sample.yaml* and *testcase.yaml* files and uses them as entry points when looking for tests. The change *sample.yaml* → *testspec.yaml* is needed to *hide* such configurations from the regular execution.

* | Standard pytest test collection rules are used for pytest tests, i.e. *.py* files are entry points.
  | Tests using existing configurations are marked with :code:`@pytest.mark.build_specification()`.
  | This decorator takes strings with configuration names to be tested as arguments.
  | The twister plugin creates variants of the decorated test for each configuration.
  | If none is given, all configurations from the *testspec.yaml* will be considered.

* | The line *harness: keyboard* is used in yamls to tell twister that a test is not executable. Hence, the need for its removal.

* | The abstraction for device adapters in twister pytest pluggin allows for writing tests
  | which are independent from a type of DUT. The test supports execution on real hardware
  | and on qemu. Bidirectional communication is not yet implemented for *native_posix*.

* | Test functions in this example are using :code:`builder` and :code:`dut` fixtures.
  | :code:`builder` calls for Zephyr's build system to prepare configurations (images) to be tested.
  | :code:`dut` setups a DUT (chosen on a higher level by twister) by flashing (executing) the chosen configuration, opening a connection (serial or FIFO file) and passing the DUT to a test.

Sample Output
=============

.. raw:: html

   <details>
   <summary>
   <a>
   Output:
   </a>
   </summary>

.. code-block:: console

      ~/zephyrproject/zephyr$ pytest --twister --zephyr-base=~/zephyrproject/zephyr ~/zephyrproject/zephyr/samples/subsys/shell/shell_module/ --platform=qemu_x86 -s --log-level=INFO -v
      Renaming output directory to /home/maciej/zephyrproject/zephyr/twister-out_230411164600
      2023-04-12 09:40:46,238:INFO:twister2.platform_specification: Reading platform configuration files under /home/maciej/zephyrproject/zephyr/boards
      2023-04-12 09:40:47,733:INFO:twister2.platform_specification: Reading platform configuration files under /home/maciej/zephyrproject/zephyr/scripts/pylib/twister/boards
      2023-04-12 09:40:48,163:INFO:twister2.environment.environment: Using 'zephyr' toolchain.
      =========================================================================================== test session starts ============================================================================================
      platform linux -- Python 3.8.14, pytest-7.2.0, pluggy-1.0.0 -- /home/maciej/twisterV2/twister/.venv/bin/python3.8
      cachedir: .pytest_cache
      rootdir: /home/maciej/zephyrproject/zephyr
      plugins: xdist-3.1.0, cov-4.0.0, rerunfailures-11.0, subtests-0.9.0, split-tests-1.1.0, twister-0.0.1, split-0.8.0
      collected 2 items

      samples/subsys/shell/shell_module/shell_test.py::test_shell_help_and_ping[qemu_x86:sample.shell.shell_module] 2023-04-12 09:40:48,227:INFO:twister2.builder.build_manager: Create empty builder status file: /home/maciej/zephyrproject/zephyr/twister-out/twister_builder.json
      2023-04-12 09:40:48,228:INFO:twister2.builder.cmake_builder: CMake command: /home/maciej/.pyenv/shims/cmake -S/home/maciej/zephyrproject/zephyr/samples/subsys/shell/shell_module -B/home/maciej/zephyrproject/zephyr/twister-out/qemu_x86/samples/subsys/shell/shell_module/sample.shell.shell_module -GNinja -DBOARD=qemu_x86 -DTC_RUNID=493f18a6e7d235917d6aafca8fc296c3 -DEXTRA_CFLAGS=-Werror '-DEXTRA_AFLAGS=-Werror -Wa,--fatal-warnings' -DEXTRA_LDFLAGS=-Wl,--fatal-warnings -DEXTRA_GEN_DEFINES_ARGS=--edtlib-Werror -DQEMU_PIPE=/home/maciej/zephyrproject/zephyr/twister-out/qemu_x86/samples/subsys/shell/shell_module/sample.shell.shell_module/qemu-fifo
      2023-04-12 09:40:53,143:INFO:twister2.builder.builder_abstract: Finished running CMake on /home/maciej/zephyrproject/zephyr/samples/subsys/shell/shell_module for qemu_x86
      2023-04-12 09:40:53,153:INFO:twister2.builder.cmake_builder: Build command: /home/maciej/.pyenv/shims/cmake --build /home/maciej/zephyrproject/zephyr/twister-out/qemu_x86/samples/subsys/shell/shell_module/sample.shell.shell_module
      2023-04-12 09:40:55,759:INFO:twister2.builder.builder_abstract: Finished running building on /home/maciej/zephyrproject/zephyr/samples/subsys/shell/shell_module for qemu_x86
      2023-04-12 09:40:55,760:INFO:twister2.device.qemu_adapter: Running command: /home/maciej/twisterV2/twister/.venv/bin/west build -d /home/maciej/zephyrproject/zephyr/twister-out/qemu_x86/samples/subsys/shell/shell_module/sample.shell.shell_module -t run
      2023-04-12 09:40:56,866:INFO:shell_test: SeaBIOS (version zephyr-v1.0.0-0-g31d4e0e-dirty-20200714_234759-fv-az50-zephyr)
      2023-04-12 09:40:56,867:INFO:shell_test: Booting from ROM..
      2023-04-12 09:40:56,868:INFO:shell_test:
      2023-04-12 09:40:56,869:INFO:shell_test:
      2023-04-12 09:40:56,875:INFO:shell_test: uart:~$ help
      2023-04-12 09:40:56,876:INFO:shell_test: Please press the <Tab> button to see all available commands.
      2023-04-12 09:40:56,881:INFO:shell_test: You can also use the <Tab> button to prompt or auto-complete all commands or its subcommands.
      2023-04-12 09:40:56,882:INFO:shell_test: You can try to call commands with <-h> or <--help> parameter for more information.
      2023-04-12 09:40:56,882:INFO:shell_test:
      2023-04-12 09:40:56,882:INFO:shell_test: Shell supports following meta-keys:
      2023-04-12 09:40:56,882:INFO:shell_test: Ctrl + (a key from: abcdefklnpuw)
      2023-04-12 09:40:56,882:INFO:shell_test: Alt  + (a key from: bf)
      2023-04-12 09:40:56,902:INFO:shell_test: Please refer to shell documentation for more details.
      2023-04-12 09:40:56,902:INFO:shell_test:
      2023-04-12 09:40:56,902:INFO:shell_test: Available commands:
      2023-04-12 09:40:56,902:INFO:shell_test: bypass              :Bypass shell
      2023-04-12 09:40:56,902:INFO:shell_test: clear               :Clear screen.
      2023-04-12 09:40:56,902:INFO:shell_test: date                :Date commands
      2023-04-12 09:40:56,902:INFO:shell_test: demo                :Demo commands
      2023-04-12 09:40:56,902:INFO:shell_test: device              :Device commands
      2023-04-12 09:40:56,902:INFO:shell_test: devmem              :Read/write physical memory
      2023-04-12 09:40:56,902:INFO:shell_test:                        Usage:
      2023-04-12 09:40:56,902:INFO:shell_test:                        Read memory at address with optional width:
      2023-04-12 09:40:56,902:INFO:shell_test:                        devmem address [width]
      2023-04-12 09:40:56,903:INFO:shell_test:                        Write memory at address with mandatory width and value:
      2023-04-12 09:40:56,903:INFO:shell_test:                        devmem address <width> <value>
      2023-04-12 09:40:56,903:INFO:shell_test: dynamic             :Demonstrate dynamic command usage.
      2023-04-12 09:40:56,903:INFO:shell_test: help                :Prints the help message.
      2023-04-12 09:40:56,903:INFO:shell_test: history             :Command history.
      2023-04-12 09:40:56,903:INFO:shell_test: kernel              :Kernel commands
      2023-04-12 09:40:56,903:INFO:shell_test: log                 :Commands for controlling logger
      2023-04-12 09:40:56,903:INFO:shell_test: log_test            :Log test
      2023-04-12 09:40:56,903:INFO:shell_test: resize              :Console gets terminal screen size or assumes default in
      2023-04-12 09:40:56,903:INFO:shell_test:                        case the readout fails. It must be executed after each
      2023-04-12 09:40:56,903:INFO:shell_test:                        terminal width change to ensure correct text display.
      2023-04-12 09:40:56,903:INFO:shell_test: section_cmd         :Demo command using section for subcommand registration
      2023-04-12 09:40:56,904:INFO:shell_test: shell               :Useful, not Unix-like shell commands.
      2023-04-12 09:40:56,904:INFO:shell_test: shell_uart_release  :Uninitialize shell instance and release uart, start
      2023-04-12 09:40:56,904:INFO:shell_test:                        loopback on uart. Shell instance is reinitialized when
      2023-04-12 09:40:56,904:INFO:shell_test:                        'x' is pressed
      2023-04-12 09:40:56,904:INFO:shell_test: stats               :Stats commands
      2023-04-12 09:40:56,904:INFO:shell_test: version             :Show kernel version
      2023-04-12 09:40:56,904:INFO:shell_test: uart:~$ demo ping
      2023-04-12 09:40:56,904:INFO:shell_test: pong
      PASSED2023-04-12 09:40:57,032:INFO:twister2.device.qemu_adapter: Running simulation terminated

      samples/subsys/shell/shell_module/shell_test.py::test_shell_introduce_self[qemu_x86:sample.shell.shell_module] 2023-04-12 09:40:57,035:INFO:twister2.builder.build_manager: Already build in /home/maciej/zephyrproject/zephyr/twister-out/qemu_x86/samples/subsys/shell/shell_module/sample.shell.shell_module
      2023-04-12 09:40:57,037:INFO:twister2.device.qemu_adapter: Running command: /home/maciej/twisterV2/twister/.venv/bin/west build -d /home/maciej/zephyrproject/zephyr/twister-out/qemu_x86/samples/subsys/shell/shell_module/sample.shell.shell_module -t run
      2023-04-12 09:40:58,146:INFO:shell_test: SeaBIOS (version zephyr-v1.0.0-0-g31d4e0e-dirty-20200714_234759-fv-az50-zephyr)
      2023-04-12 09:40:58,147:INFO:shell_test: Booting from ROM..
      2023-04-12 09:40:58,148:INFO:shell_test:
      2023-04-12 09:40:58,148:INFO:shell_test:
      2023-04-12 09:40:58,159:INFO:shell_test: uart:~$ demo board
      2023-04-12 09:40:58,174:INFO:shell_test: qemu_x86
      PASSED2023-04-12 09:40:58,288:INFO:twister2.device.qemu_adapter: Running simulation terminated


      -------------------------------------------------------- generated results report file: /home/maciej/zephyrproject/zephyr/twister-out/testplan.json --------------------------------------------------------
      -------------------------------------------------------- generated results report file: /home/maciej/zephyrproject/zephyr/twister-out/twister.json ---------------------------------------------------------
      ============================================================================================ 2 passed in 10.13s ============================================================================================


.. raw:: html

   </details>
